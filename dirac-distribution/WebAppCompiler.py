"""
It is used to compile the web framework
"""
from contextlib import contextmanager
import gzip
import json
import logging
import os
from os.path import isdir, isfile, join
import shlex
import shutil
import subprocess
import tempfile

from diraccfg import CFG

logging.basicConfig(level=logging.INFO)


class WebAppCompiler():
    def __init__(self, name, destination, extjspath=None, py3_style=False):
        if extjspath is None:
            extjspath='/ext-6.2.0/'

        self._name = name
        self._destination = destination
        self._sdkPath = extjspath
        self._py3_style = py3_style

        self._extVersion = '6.2.0'
        self._extDir = 'extjs'    # this directory will contain all the resources required by ExtJS

        self._webAppPath = join(destination, 'WebAppDIRAC', 'WebApp')
        self._allStaticPaths = [join(self._webAppPath, 'static')]
        if self._name != 'WebAppDIRAC':
            self._allStaticPaths.append(join(name.join(destination.rsplit('WebAppDIRAC', 1)), name, 'WebApp', 'static'))
        if self._py3_style:
            self._staticPathsToCompile = [self._allStaticPaths[-1]]
        else:
            self._staticPathsToCompile = self._allStaticPaths[:]

        self._classPaths = [
            join(self._webAppPath, "static", "core", "js", "utils"),
            join(self._webAppPath, "static", "core", "js", "core"),
            join(extjspath, "build/ext-all-debug.js"),
            join(extjspath, "build/packages/ux/classic/ux-debug.js"),
            join(extjspath, "build/packages/charts/classic/charts-debug.js"),
        ]

        self._extjsDirsToCopy = [
            join(extjspath, "build/packages"),
            join(extjspath, "build/classic"),
        ]

        self._extjsFilesToCopy = [
            join(extjspath, "build/ext-all.js"),
            join(extjspath, "build/ext-all-debug.js"),
            join(extjspath, "build/packages/ux/classic/ux-debug.js"),
        ]

        self._compileTemplate = "/CompileTemplates"
        if not os.path.exists(self._compileTemplate):
            logging.error('CompileTemplates used to compile JS does not exists!')

        self._appDependency = {}

    def _deployResources(self, webAppPath=None):
        """
        This method copy the required files and directories to the appropriate place
        """
        extjsDirPath = join(webAppPath or self._webAppPath, 'static', self._extDir)
        if not os.path.exists(extjsDirPath):
            try:
                os.makedirs(extjsDirPath)
            except OSError as e:
                logging.error(f"Can not create release extjs {e!r}")
                raise RuntimeError("Can not create release extjs" + repr(e))
        for dirSrc in self._extjsDirsToCopy:
            destDir = join(extjsDirPath, os.path.split(dirSrc)[1])
            try:
                shutil.copytree(dirSrc, destDir)
            except OSError as e:
                if e.errno != 17:
                    raise RuntimeError(f"Can not copy {dirSrc} directory to {destDir}: {e!r}")
                else:
                    logging.error(f"{destDir} directory already exists. It will be not overwritten!")

        for filePath in self._extjsFilesToCopy:
            try:
                shutil.copy(filePath, extjsDirPath)
            except (IOError, OSError) as e:
                logging.error(f"Can not copy {filePath} file to {extjsDirPath}: {e!r}")

    def _writeINFile(self, tplName, extra={}):
        """
        It creates a temporary file using different templates. For example: /tmp/zmathe/tmp4sibR5.compilejs.app.tpl
        This is required to compile the web framework.

        :params str tplName: it is the name of the template
        :params dict extra: it contains the application location, which will be added to the temporary file
        :return: the location of the file
        """
        inTpl = join(self._compileTemplate, tplName)
        with open(inTpl) as infd:
            data = infd.read()
        data = data.replace("%EXT_VERSION%", self._extVersion)
        for k, v in extra.items():
            data = data.replace(f"%{k.upper()}%", v)
        with tempfile.NamedTemporaryFile(mode="wt", suffix=f".compilejs.{tplName}", delete=False) as fp:
            fp.write(data)
            return fp.name

    @contextmanager
    def _applyExtJSConfig(self, overridesPath=None):
        """
        Setup sencha package configuration, restoring the original afterwards
        :param str overridesPath: path to directory used for overrides
        """
        packageConfigFn = join(self._sdkPath, "package.json")
        with open(join(self._sdkPath, "package.json")) as fp:
            packageConfig = json.load(fp)

        if overridesPath:
            logging.info(f"Applying overrides from {overridesPath}")
            packageConfig["overrides"] = overridesPath

        packageConfig["language"] = {"js": {"output": "ES6"}}

        shutil.copyfile(packageConfigFn, f"{packageConfigFn}.bak")
        try:
            with open(join(self._sdkPath, "package.json"), "wt") as fp:
                json.dump(packageConfig, fp)
            yield
        finally:
            shutil.copyfile(f"{packageConfigFn}.bak", packageConfigFn)

    def _compileApp(self, extPath, extName, appName, extClassPath=""):
        """
        It compiles an application
        :param str extPath: directory full path, which contains the applications
                            for example: /tmp/zmathe/tmpFxr5LzDiracDist/WebAppDIRAC/WebApp/static/DIRAC
        :param str extName: the name of the application for example: DIRAC or LHCbDIRAC, etc
        :param str appName: the name of the application for example: Accounting
        :param str extClassPath: if we compile an extension, we can provide the class path of the base class
        """
        inFile = self._writeINFile("app.tpl", {'APP_LOCATION': f'{extName}.{appName}.classes.{appName}'})
        buildDir = join(extPath, appName, 'build')
        try:
            shutil.rmtree(buildDir)
        except OSError:
            pass
        os.makedirs(buildDir, exist_ok=True)
        outFile = join(buildDir, "index.html")
        compressedJsFile = join(buildDir, appName + '.js')

        classPath = list(self._classPaths)
        excludePackage = f",{extName}.*"
        if extClassPath != "":
            classPath.append(extClassPath)
            excludePackage = f",DIRAC.*,{extName}.*"

        classPath.append(join(extPath, appName, "classes"))

        cmd = ['sencha', '-sdk', self._sdkPath, 'compile', f"-classpath={','.join(classPath)}",
                'page', '-name=page', '-input-file', inFile, '-out', outFile, 'and',
                'restore', 'page', 'and', 'exclude', '-not', '-namespace', f'Ext.dirac.*{excludePackage}', 'and',
                'concat', '-yui', compressedJsFile]
        with self._applyExtJSConfig(join(extPath, appName, "overrides")):
            subprocess.check_call(cmd)

    def _zip(self, staticPath, stack=""):
        """
        It compress the compiled applications
        """
        c = 0
        l = "|/-\\"
        for entry in os.listdir(staticPath):
            n = stack + l[c % len(l)]
            if entry[-3:] == ".gz":
                continue
            ePath = join(staticPath, entry)
            if isdir(ePath):
                self._zip(ePath, n)
                continue
            zipPath = f"{ePath}.gz"
            if isfile(zipPath) and os.stat(zipPath).st_mtime > os.stat(ePath).st_mtime:
                continue
            c += 1
            with gzip.open(zipPath, "wb", 9) as outFp, open(ePath, "rb") as inFp:
                while buf := inFp.read(8192):
                    outFp.write(buf)

    def run(self):
        """
        This compiles the web framework
        """
        if self._py3_style:
            if self._name == "DIRACWebAppResources":
                logging.info("Running _deployResources for %s", self._name)
                self._deployResources(join(self._destination, self._name, 'WebApp'))
                logging.info("Zipping static files")
                self._zip(join(self._destination, self._name, 'WebApp', "static"))
                logging.info("Done")
                return
            logging.info("Skipping _deployResources as in Python 3 style but not packaging DIRACWebAppResources")
        else:
            self._deployResources()

        # we are compiling an extension of WebAppDIRAC
        if self._name != 'WebAppDIRAC':
            self._appDependency.update(self.getAppDependencies())
        staticPath = join(self._webAppPath, "static")
        logging.info(f"Compiling core: {staticPath}")

        outFile = join(staticPath, "core", "build", "index.html")
        if os.path.isfile(outFile):
            logging.info(f"Skipping generation of {outFile} as it already exists")
        else:
            inFile = self._writeINFile("core.tpl")
            buildDir = join(staticPath, "core", "build")
            try:
                shutil.rmtree(buildDir)
            except OSError:
                pass
            logging.info(f" IN file written to {inFile}")

            cmd = ["sencha", "-sdk", self._sdkPath, "compile", f"-classpath={','.join(self._classPaths)}",
                "page", "-yui", "-input-file", inFile, "-out", outFile]
            logging.info("Running %s", shlex.join(cmd))
            with self._applyExtJSConfig():
                subprocess.check_call(cmd)

            try:
                os.unlink(inFile)
            except IOError:
                pass

        for staticPath in self._staticPathsToCompile:
            logging.info(f"Looking into {staticPath}")
            extDirectoryContent = os.listdir(staticPath)
            if len(extDirectoryContent) == 0:
                raise RuntimeError("The extension directory is empty:" + str(staticPath))

            extNames = [ext for ext in extDirectoryContent if 'DIRAC' in ext]
            if len(extNames) > 1:
                extNames.remove('DIRAC')
            extName = extNames[-1]
            logging.info(f"Detected extension:{extName}")

            extPath = join(staticPath, extName)
            if not isdir(extPath):
                continue
            logging.info(f"Exploring {extName}")
            for appName in os.listdir(extPath):
                expectedJS = join(extPath, appName, "classes", f"{appName}.js")
                if not isfile(expectedJS):
                    continue
                classPath = self._getClasspath(extName, appName)
                logging.info(f"Trying to compile {extName}.{appName}.classes.{appName} CLASSPATH={classPath}")
                self._compileApp(extPath, extName, appName, classPath)

        logging.info("Zipping static files")
        self._zip(staticPath)
        logging.info("Done")

    def _getClasspath(self, extName, appName):
        classPath = ''
        dependency = self._appDependency.get(f"{extName}.{appName}", "")

        if dependency != "":
            depPath = dependency.split(".")
            for staticPath in self._allStaticPaths:
                expectedJS = join(staticPath, depPath[0], depPath[1], "classes")
                logging.info(expectedJS)
                if not isdir(expectedJS):
                    continue
                classPath = expectedJS
        return classPath

    def getAppDependencies(self):
        """
        Generate the dependency dictionary

        :return: dict of dependencies
        """
        webcfg = self._loadWebAppCFGFiles(self._name)
        dependencyCFG = webcfg['WebApp']['Dependencies']
        # CFG objects resembles dictionaries, but they are not
        # so, we can't just do "return dependencyCFG"
        return {
            opName: dependencyCFG[opName]
            for opName in dependencyCFG
        }

    def _loadWebAppCFGFiles(self, extension):
        """
        Load WebApp/web.cfg definitions

        :param str extension: the module name of the extension of WebAppDirac for example: LHCbWebDIRAC
        """
        webCFG = CFG()
        for modName in ["WebAppDIRAC", extension]:
            cfgPath = join(modName.join(self._destination.rsplit('WebAppDIRAC', 1)), modName, "WebApp", "web.cfg")
            if not isfile(cfgPath):
                logging.info(f"Web configuration file {cfgPath} does not exists!")
                continue
            try:
                modCFG = CFG().loadFromFile(cfgPath)
            except Exception as e:
                logging.error(f"Could not load {cfgPath}: {e}")
                continue
            logging.info(f"Loaded {cfgPath}")
            expl = ["/WebApp"]
            while expl:
                current = expl.pop(0)
                if not modCFG.isSection(current):
                    continue
                if modCFG.getOption(f"{current}/AbsoluteDefinition", False):
                    logging.info(f"{modName}:{current} is an absolute definition")
                    try:
                        webCFG.deleteKey(current)
                    except Exception:
                        pass
                    modCFG.deleteKey(f"{current}/AbsoluteDefinition")
                else:
                    expl += [f"{current}/{sec}" for sec in modCFG[current].listSections()]
            # Add the modCFG
            webCFG = webCFG.mergeWith(modCFG)
        return webCFG
