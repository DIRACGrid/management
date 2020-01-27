#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################################
# File :    dirac-create-distribution-tarball
# Author :  Federico Stagni
########################################################################
"""
    Create tarballs for a given DIRAC release
"""
import sys
import os
import shutil
import tempfile
import subprocess
import shlex
import logging
import argparse
import docutils.core

from Distribution import parseVersionString, writeVersionToInit, createTarball
from WebAppCompiler import WebAppCompiler

logging.basicConfig(level=logging.INFO)

VALID_VCS = ('svn', 'git', 'hg', 'file')

parser = argparse.ArgumentParser()

parser.add_argument("-v", "--version", help="version to tar")
parser.add_argument("-u", "--sourceURL", help="VCS path to retrieve sources from")
parser.add_argument("-D", "--destination", help="Destination where to build the tar files")
parser.add_argument("-n", "--name", help="Tarball name")
parser.add_argument("-z", "--vcs", help="VCS to use to retrieve the sources (try to find out if not specified)")
parser.add_argument("-b", "--vcsBranch", help="VCS branch (if needed)")
parser.add_argument("-p", "--vcsPath", help="VCS path (if needed)")
parser.add_argument("-K", "--relNotes", help="Path to the release notes")
parser.add_argument("-A", "--outRelNotes",
                    action="store_true",
                    help="Leave a copy of the compiled release notes outside the tarball")
parser.add_argument("-e", "--extensionVersion",
                    help="if we have an extension, we can provide the base module version, (if it is needed)")
parser.add_argument("-E", "--extensionSource",
                    help="if we have an extension we must provide code repository url")
parser.add_argument("-P", "--extjspath", help="directory of the extjs library")


args = parser.parse_args()
args.destination == os.path.realpath(args.destination)
if args.vcs == 'subversion':
    args.vcs = 'svn'
elif args.vcs == 'mercurial':
    args.vcs = 'hg'


def isOK():
    if not args.version:
        raise RuntimeError("No version defined")
    if not args.sourceURL:
        raise RuntimeError("No Source URL defined")
    if not args.name:
        raise RuntimeError("No name defined")
    if args.vcs and args.vcs not in VALID_VCS:
        raise RuntimeError("Invalid VCS %s" % args.vcs)


def _checkDestination():
    if not args.destination:
        args.destination = tempfile.mkdtemp('DIRACTarball')

    logging.info("Will generate tarball in %s" % args.destination)


def _discoverVCS():
    sourceURL = args.sourceURL
    if os.path.expanduser(sourceURL).find("/") == 0:
        sourceURL = os.path.expanduser(sourceURL)
        args.vcs = "file"
        return True
    if sourceURL.find(".git") == len(sourceURL) - 4:
        args.vcs = "git"
        return True
    for vcs in VALID_VCS:
        if sourceURL.find(vcs) == 0:
            args.vcs = vcs
            return True
    return False


def _checkoutSource(moduleName=None, sourceURL=None, tagVersion=None):
    """
    This method will checkout a given module from a given repository: svn, hg, git

    :param str moduleName: The name of the Module: for example: LHCbWebDIRAC
    :param str sourceURL: The code repository: ssh://git@gitlab.cern.ch:7999/lhcb-dirac/LHCbWebDIRAC.git
    :param str tagVersion: the tag for example: v4r3p6
    """
    if not args.vcs:
        if not _discoverVCS():
            raise RuntimeError("Could not autodiscover VCS")
    logging.info("Checking out using %s method" % args.vcs)

    if args.vcs == "file":
        return _checkoutFromFile(moduleName, sourceURL)
    elif args.vcs == "svn":
        return _checkoutFromSVN(moduleName, sourceURL, tagVersion)
    elif args.vcs == "hg":
        return _checkoutFromHg(moduleName, sourceURL)
    elif args.vcs == "git":
        return _checkoutFromGit(moduleName, sourceURL, tagVersion)

    raise RuntimeError("OOPS. Unknown VCS %s!" % args.vcs)


def _checkoutFromFile(moduleName=None, sourceURL=None):
    """
    This method checkout a given tag from a file
    Note: we can checkout any project form a file

    :param str moduleName: The name of the Module
    :param str sourceURL: The code repository

    """
    if not moduleName:
        moduleName = args.name

    if not sourceURL:
        sourceURL = args.sourceURL

    if sourceURL.find("file://") == 0:
        sourceURL = sourceURL[7:]
    sourceURL = os.path.realpath(sourceURL)
    pyVer = sys.version_info
    if pyVer[0] == 2 and pyVer[1] < 6:
        shutil.copytree(
            sourceURL,
            os.path.join(args.destination, moduleName),
            symlinks=True)
    else:
        shutil.copytree(
            sourceURL,
            os.path.join(args.destination, moduleName),
            symlinks=True,
            ignore=shutil.ignore_patterns('.svn', '.git', '.hg', '*.pyc', '*.pyo'))


def _checkoutFromSVN(moduleName=None, sourceURL=None, tagVersion=None):
    """
    This method checkout a given tag from a SVN repository.
    Note: we can checkout any project form a SVN repository

    :param str moduleName: The name of the Module
    :param str sourceURL: The code repository
    :param str tagVersion: the tag for example: v4r3p6

    """

    if not moduleName:
        moduleName = args.name

    if not sourceURL:
        sourceURL = args.sourceURL

    if not tagVersion:
        tagVersion = args.version

    cmd = "svn export --trust-server-cert --non-interactive '%s/%s' '%s'" % (
        sourceURL,
        tagVersion,
        os.path.join(args.destination, moduleName))
    logging.debug("Executing: %s" % cmd)
    subprocess.systemCall(900, shlex.split(cmd))


def _checkoutFromHg(moduleName=None, sourceURL=None):
    """
    This method checkout a given tag from a hg repository.
    Note: we can checkout any project form a hg repository

    :param str moduleName: The name of the Module
    :param str sourceURL: The code repository

    """
    if not moduleName:
        moduleName = args.name

    if not sourceURL:
        sourceURL = args.sourceURL

    if args.vcsBranch:
        brCmr = "-b %s" % args.vcsBranch
    else:
        brCmr = ""
    fDirName = os.path.join(args.destination, moduleName)
    cmd = "hg clone %s '%s' '%s.tmp1'" % (brCmr, sourceURL, fDirName)
    logging.debug("Executing: %s" % cmd)
    if os.system(cmd):
        raise RuntimeError("Error while retrieving sources from hg")

    hgArgs = ["--cwd '%s.tmp1'" % fDirName]
    if args.vcsPath:
        hgArgs.append("--include '%s/*'" % args.vcsPath)
    hgArgs.append("'%s.tmp2'" % fDirName)

    cmd = "hg archive %s" % " ".join(hgArgs)
    logging.debug("Executing: %s" % cmd)
    exportRes = os.system(cmd)
    shutil.rmtree("%s.tmp1" % fDirName)

    if exportRes:
        raise RuntimeError("Error while exporting from hg")

    # TODO: tmp2/path to dest
    source = "%s.tmp2" % fDirName
    if args.vcsPath:
        source = os.path.join(source, args.vcsPath)

    if not os.path.isdir(source):
        shutil.rmtree("%s.tmp2" % fDirName)
        raise RuntimeError("Path %s does not exist in repo")

    os.rename(source, fDirName)
    shutil.rmtree("%s.tmp2" % fDirName)


def replaceKeywordsWithGit(dirToDo):
    for fileName in os.listdir(dirToDo):
        objPath = os.path.join(dirToDo, fileName)
        if os.path.isdir(objPath):
            replaceKeywordsWithGit(objPath)
        elif os.path.isfile(objPath):
            if fileName.find('.py', len(fileName) - 3) == len(fileName) - 3:
                with open(objPath, "r", encoding="utf-8") as fd:
                    fileContents = fd.read()
                for keyWord, cmdArgs in (('$Id$', '--pretty="%h (%ad) %an <%aE>" --date=iso'),
                                         ('$SHA1$', '--pretty="%H"')):
                    foundKeyWord = fileContents.find(keyWord)
                    if foundKeyWord > -1:
                        cmd = shlex.split("git log -n 1 %s %s" % (cmdArgs, fileName))
                        po2 = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=dirToDo)
                        po2.wait()
                        if po2.returncode:
                            continue
                        toReplace = po2.stdout.read().decode()
                        toReplace = toReplace.strip()
                        toReplace = "".join(i for i in toReplace if ord(i) < 128)
                        fileContents = fileContents.replace(keyWord, toReplace, 1)

                with open(objPath, "wb") as fd:
                    fd.write(fileContents.encode())


def _checkoutFromGit(moduleName=None, sourceURL=None, tagVersion=None):
    """
    This method checkout a given tag from a git repository.
    Note: we can checkout any project form a git repository

    :param str moduleName: The name of the Module: for example: LHCbWebDIRAC
    :param str sourceURL: The code repository: ssh://git@gitlab.cern.ch:7999/lhcb-dirac/LHCbWebDIRAC.git
    :param str tagVersion: the tag for example: v4r3p6

    """

    if not moduleName:
        moduleName = args.name

    if not sourceURL:
        sourceURL = args.sourceURL

    if not tagVersion:
        tagVersion = args.version

    if args.vcsBranch:
        brCmr = "-b %s" % args.vcsBranch
    else:
        brCmr = ""
    fDirName = os.path.join(args.destination, moduleName)
    cmd = "git clone %s '%s' '%s'" % (brCmr, sourceURL, fDirName)

    logging.debug("Executing: %s" % cmd)
    if os.system(cmd):
        raise RuntimeError("Error while retrieving sources from git")

    branchName = "DIRACDistribution-%s" % os.getpid()

    isTagCmd = "( cd '%s'; git tag -l | grep '%s' )" % (fDirName, tagVersion)
    if os.system(isTagCmd):
        # No tag found, assume branch
        branchSource = 'origin/%s' % tagVersion
    else:
        branchSource = tagVersion

    cmd = "( cd '%s'; git checkout -b '%s' '%s' )" % (fDirName, branchName, branchSource)

    logging.debug("Executing: %s" % cmd)
    exportRes = os.system(cmd)

    # Add the keyword substitution
    logging.info("Replacing keywords (can take a while)...")
    replaceKeywordsWithGit(fDirName)

    shutil.rmtree("%s/.git" % fDirName, ignore_errors=True)
    shutil.rmtree("%s/docs" % fDirName, ignore_errors=True)
    shutil.rmtree("%s/docs" % args.destination, ignore_errors=True)

    if exportRes:
        raise RuntimeError("Error while exporting from git")


def _loadReleaseNotesFile():
    if not args.relNotes:
        relNotes = os.path.join(args.destination, args.name, "release.notes")
    else:
        relNotes = args.relNotes
    if not os.path.isfile(relNotes):
        return
    with open(relNotes, encoding='utf-8') as fd:
        releaseContents = fd.readlines()
    logging.info("Loaded %s" % relNotes)
    relData = []
    version = False
    feature = False
    lastKey = False
    for rawLine in releaseContents:
        line = rawLine.strip()
        if not line:
            continue
        if line[0] == "[" and line[-1] == "]":
            version = line[1:-1].strip()
            relData.append((version, {'comment': [], 'features': []}))
            feature = False
            lastKey = False
            continue
        if line[0] == "*":
            feature = line[1:].strip()
            relData[-1][1]['features'].append([feature, {}])
            lastKey = False
            continue
        if not feature:
            relData[-1][1]['comment'].append(rawLine)
            continue
        keyDict = relData[-1][1]['features'][-1][1]
        foundKey = False
        for key in ('BUGFIX', 'BUG', 'FIX', "CHANGE", "NEW", "FEATURE"):
            if line.find("%s:" % key) == 0:
                line = line[len(key) + 2:].strip()
            elif line.find("%s " % key) == 0:
                line = line[len(key) + 1:].strip()
            else:
                continue
            foundKey = key
            break

        if foundKey in ('BUGFIX', 'BUG', 'FIX'):
            foundKey = 'BUGFIX'
        elif foundKey in ('NEW', 'FEATURE'):
            foundKey = 'FEATURE'

        if foundKey:
            if foundKey not in keyDict:
                keyDict[foundKey] = []
            keyDict[foundKey].append(line)
            lastKey = foundKey
        elif lastKey:
            keyDict[lastKey][-1] += " %s" % line

    return relData


def _generateRSTFile(releaseData, rstFileName, pkgVersion, singleVersion):
    rstData = []
    parsedPkgVersion = parseVersionString(pkgVersion)
    for version, verData in releaseData:
        if singleVersion and version != pkgVersion:
            continue
        if parseVersionString(version) > parsedPkgVersion:
            continue
        versionLine = "Version %s" % version
        rstData.append("")
        rstData.append("=" * len(versionLine))
        rstData.append(versionLine)
        rstData.append("=" * len(versionLine))
        rstData.append("")
        if verData['comment']:
            rstData.append("\n".join(verData['comment']))
            rstData.append("")
        for feature, featureData in verData['features']:
            if not featureData:
                continue
            rstData.append(feature)
            rstData.append("=" * len(feature))
            rstData.append("")
            for key in sorted(featureData):
                rstData.append(key.capitalize())
                rstData.append(":" * (len(key) + 5))
                rstData.append("")
                for entry in featureData[key]:
                    rstData.append(" - %s" % entry)
                rstData.append("")
    # Write releasenotes.rst
    rstFilePath = os.path.join(args.destination, args.name, rstFileName)
    with open(rstFilePath, "wb") as fd:
        fd.write("\n".join(rstData).encode())


def _compileReleaseNotes(rstFile):

    relNotesRST = os.path.join(args.destination, args.name, rstFile)
    if not os.path.isfile(relNotesRST):
        if args.relNotes:
            raise RuntimeError("Defined release notes %s do not exist!" % args.relNotes)
        raise RuntimeError("No release notes found in %s. Skipping" % relNotesRST)
    # Find basename
    baseRSTFile = rstFile
    for ext in ('.rst', '.txt'):
        if baseRSTFile[-len(ext):] == ext:
            baseRSTFile = baseRSTFile[:-len(ext)]
            break
    baseNotesPath = os.path.join(args.destination, args.name, baseRSTFile)
    # To HTML
    with open(relNotesRST, encoding='utf-8') as fd:
        rstData = fd.read()
    parts = docutils.core.publish_parts(rstData, writer_name='html')
    baseList = [baseNotesPath]
    if args.outRelNotes:
        logging.info("Leaving a copy of the release notes outside the tarballs")
        baseList.append("%s/%s.%s.%s" % (args.destination, baseRSTFile, args.name, args.version))
    for baseFileName in baseList:
        htmlFileName = baseFileName + ".html"
        with open(htmlFileName, "wb") as fd:
            fd.write(parts['whole'].encode())
        # To pdf -- disabled because rst2pdf is not python 3
        # pdfCmd = "rst2pdf '%s' -o '%s.pdf'" % (relNotesRST, baseFileName)
        # logging.debug("Executing %s" % pdfCmd)
        # if os.system(pdfCmd):
        #     logging.critical("Could not generate PDF version of %s" % baseNotesPath)
    # Unlink if not necessary
    if False and not args.relNotes:
        try:
            os.unlink(relNotesRST)
        except Exception:
            pass


def _generateReleaseNotes():
    releaseData = _loadReleaseNotesFile()
    # if not releaseData:
    #     logging.info("release.notes not found. Trying to find releasenotes.rst")
    #     for rstFileName in ("releasenotes.rst", "releasehistory.rst"):
    #         _compileReleaseNotes(rstFileName)
    #         logging.info("Compiled %s file!" % rstFileName)
    #     return
    if not releaseData:
        logging.warn("No release.notes file found")
        return
    logging.info("Loaded release.notes")
    for rstFileName, singleVersion in (("releasenotes.rst", True),
                                       ("releasehistory.rst", False)):
        _generateRSTFile(releaseData, rstFileName, args.version, singleVersion)
        _compileReleaseNotes(rstFileName)
        logging.info("Compiled %s file!" % rstFileName)


def _generateTarball():
    destDir = args.destination
    tarName = "%s-%s.tar.gz" % (args.name, args.version)
    tarfilePath = os.path.join(destDir, tarName)
    dirToTar = os.path.join(args.destination, args.name)
    if args.name in os.listdir(dirToTar):
        dirToTar = os.path.join(dirToTar, args.name)
    writeVersionToInit(dirToTar, args.version)
    createTarball(tarfilePath, dirToTar)
    # Remove package dir
    shutil.rmtree(dirToTar)
    logging.info("Tar file %s created" % tarName)
    return tarfilePath


def create():
    isOK()
    _checkDestination()
    _checkoutSource()
    shutil.rmtree("%s/docs" % args.destination, ignore_errors=True)
    if args.version not in ('integration', 'master'):
        _generateReleaseNotes()

    if 'Web' in args.name and args.name != 'Web':
        # if we have an extension, we have to download, because it will be
        # required to compile the code
        if args.extensionVersion and args.extensionSource:
            # if extensionSource is not provided, the default one is used. args.soureURL....
            _checkoutSource("WebAppDIRAC", args.extensionSource, args.extensionVersion)
        WebAppCompiler(args.name, args.destination, args.extjspath).run()

    return _generateTarball()


if __name__ == "__main__":

    result = create()
    logging.info("Tarball successfully created at %s" % result)
    sys.exit(0)
