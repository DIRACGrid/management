#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################################
# File :    dirac-distribution
# Author :  Federico Stagni
########################################################################
"""
    Create tarballs for a given DIRAC release
"""

# pylint: disable=missing-docstring

import os
import tempfile
import hashlib
import logging
import argparse

from dirac_install import ReleaseConfig

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument("-r", "--release", help="release to build (mandatory)")
parser.add_argument("-l", "--project", help="Project to build the release for (DIRAC by default)", default='DIRAC')
parser.add_argument("-C", "--relcfg", help="Use <file> as the releases.cfg")
parser.add_argument("-M", "--defaultsURL", help="Where to retrieve the global defaults from", default='')
parser.add_argument("-E", "--extjspath", help="directory of the extjs library", default='')

args = parser.parse_args()


relConf = ReleaseConfig(projectName=args.project,
                        globalDefaultsURL=args.defaultsURL)
relConf.setDebugCB(logging.info)
relConf.loadProjectDefaults()

destination = tempfile.mkdtemp('DiracDist')
logging.info("Will generate tarballs in %s" % destination)


def createModuleTarballs():
    result = relConf.getModulesForRelease(args.release)
    if not result['OK']:
        raise RuntimeError(result['Message'])
    modsToTar = result['Value']
    for modName in modsToTar:
        modVersion = modsToTar[modName]
        dctArgs = ['-A']    # Leave a copy of the release notes outside the tarballs
        # Version
        dctArgs.append("-n '%s'" % modName)
        dctArgs.append("-v '%s'" % modVersion)
        logging.info("Creating tar for %s version %s" % (modName, modVersion))
        if 'Web' in modName:    # we have to compile WebApp and also its extension.
            if modName != 'WebAppDIRAC' and modName != "Web":    # it means we have an extension!
                # Note: the old portal called Web
                modules = relConf.diracBaseModules
                webData = modules.get("WebAppDIRAC", None)
                if webData:
                    dctArgs.append("-e '%s'" % webData.get("Version"))
                    dctArgs.append("-E '%s'" % webData.get("sourceUrl"))

            if args.extjspath:
                dctArgs.append("--extjspath=%s" % args.extjspath)

        # Source
        result = relConf.getModSource(args.release, modName)
        if not result['OK']:
            raise RuntimeError(result['Message'])
        modSrcTuple = result['Value']
        if modSrcTuple[0]:
            logMsgVCS = modSrcTuple[0]
            dctArgs.append("-z '%s'" % modSrcTuple[0])
        else:
            logMsgVCS = "autodiscover"
        dctArgs.append("-u '%s'" % modSrcTuple[1])
        logging.info("Sources will be retrieved from %s (%s)" % (modSrcTuple[1], logMsgVCS))
        # Tar destination
        dctArgs.append("-D '%s'" % destination)
        # Script location discovery
        scriptName = os.path.join(os.path.dirname(__file__), "dirac-create-distribution-tarball.py")
        cmd = "python3 %s %s" % (scriptName, " ".join(dctArgs))
        logging.debug("Executing %s" % cmd)
        if os.system(cmd) != 0:
            raise RuntimeError("Failed creating tarball for module %s. Aborting" % modName)
        logging.info("Tarball for %s version %s created" % (modName, modVersion))


def doTheMagic():
    logging.info("Loading releases.cfg")
    result = relConf.loadProjectRelease(
        [args.release],
        releaseMode=True,
        relLocation=args.relcfg)
    if not result['OK']:
        logging.critical("There was an error when loading the releases.cfg file: %s" % result['Message'])
        raise RuntimeError("There was an error when loading the releases.cfg file: %s" % result['Message'])
    # Module tars
    createModuleTarballs()
    # Write the releases files
    projectCFG = relConf.getReleaseCFG(args.project, args.release)
    projectCFGData = projectCFG.toString() + "\n"
    with open(os.path.join(destination, "release-%s-%s.cfg" % (args.project, args.release)), "wb") as relFile:
        relFile.write(projectCFGData.encode())
    with open(os.path.join(destination, "release-%s-%s.md5" % (args.project, args.release)), "wb") as relFile:
        relFile.write(hashlib.md5(projectCFGData.encode()).hexdigest().encode())
    # Check deps
    if args.project != 'DIRAC':
        deps = relConf.getReleaseDependencies(args.project, args.release)
        if 'DIRAC' not in deps:
            logging.info("Release %s doesn't depend on DIRAC. Check it's what you really want" % args.release)
        else:
            logging.info("Release %s depends on DIRAC %s" % (args.release, deps['DIRAC']))


def getUploadCmd():
    result = relConf.getUploadCommand()
    upCmd = ''
    if result['OK']:
        upCmd = result['Value']

    filesToCopy = []
    for fileName in os.listdir(destination):
        for ext in (".tar.gz", ".md5", ".cfg", ".html", ".pdf"):
            if fileName.find(ext) == len(fileName) - len(ext):
                filesToCopy.append(os.path.join(destination, fileName))
    outFiles = " ".join(filesToCopy)
    outFileNames = " ".join([os.path.basename(filePath) for filePath in filesToCopy])

    if not upCmd:
        return "Upload to your installation source:\n'%s'\n" % "' '".join(filesToCopy)
    for inRep, outRep in (("%OUTLOCATION%", destination),
                          ("%OUTFILES%", outFiles),
                          ("%OUTFILENAMES%", outFileNames)):
        upCmd = upCmd.replace(inRep, outRep)
    return upCmd


if __name__ == "__main__":
    doTheMagic()
    logging.info("Everything seems ok. Tarballs generated in %s" % destination)
    upCmd = getUploadCmd()
    print(upCmd)
