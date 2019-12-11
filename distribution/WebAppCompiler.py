"""
It is used to compile the web framework
"""

import os
import tempfile
import shutil
import subprocess
import gzip
import logging

# from DIRAC import gConfig
# from DIRAC.Core.Utilities.CFG import CFG


class WebAppCompiler():

  def __init__(self, name, destination, extjspath=None):

    self.__extVersion = '6.2.0'
    self.__extDir = 'extjs'  # this directory will contain all the resources required by ExtJS
    if not extjspath:
      extjspath = '/ext-6.2.0/'

    self.__webAppPath = os.path.join(destination, 'WebAppDIRAC', 'WebApp')
    self.__staticPaths = [os.path.join(self.__webAppPath, 'static')]
    if name != 'WebAppDIRAC':
      self.__staticPaths.append(os.path.join(destination, name, 'WebApp', 'static'))

    self.__classPaths = [os.path.join(self.__webAppPath, *p) for p in (("static", "core", "js", "utils"),
                                                                       ("static", "core", "js", "core"))]
    self.__extjsDirsToCopy = []
    self.__extjsFilesToCopy = []

    self.__classPaths.append(os.path.join(os.path.dirname(extjspath), "build/ext-all-debug.js"))
    self.__classPaths.append(os.path.join(os.path.dirname(extjspath), "build/packages/ux/classic/ux-debug.js"))
    self.__classPaths.append(
        os.path.join(os.path.dirname(extjspath), "build/packages/charts/classic/charts-debug.js"))
    self.__sdkPath = extjspath
    self.__extjsDirsToCopy.append(os.path.join(os.path.dirname(extjspath), "build/packages"))
    self.__extjsDirsToCopy.append(os.path.join(os.path.dirname(extjspath), "build/classic"))
    self.__extjsFilesToCopy.append(os.path.join(os.path.dirname(extjspath), "build/ext-all.js"))
    self.__extjsFilesToCopy.append(os.path.join(os.path.dirname(extjspath), "build/ext-all-debug.js"))
    self.__extjsFilesToCopy.append(
        os.path.join(os.path.dirname(extjspath), "build/packages/ux/classic/ux-debug.js"))

    self.__compileTemplate = os.path.join(destination, 'WebAppDIRAC', "Lib", "CompileTemplates")

    self.__appDependency = {}
    self.__dependencySection = "Dependencies"

  def __deployResources(self):
    """
    This method copy the required files and directories to the appropriate place
    """
    extjsDirPath = os.path.join(self.__webAppPath, 'static', self.__extDir)
    if not os.path.exists(extjsDirPath):
      try:
        os.mkdir(extjsDirPath)
      except OSError as e:
        logging.error("Can not create release extjs", repr(e))
        raise RuntimeError("Can not create release extjs" + repr(e))
    for dirSrc in self.__extjsDirsToCopy:
      try:
        os.makedirs(os.path.join(extjsDirPath, os.path.split(dirSrc)[1]))
        shutil.copytree(dirSrc, os.path.join(extjsDirPath, os.path.split(dirSrc)[1]))
      except OSError as e:
        if e.errno != 17:
          errorMsg = "Can not copy %s directory to %s: %s" % (
              dirSrc, os.path.join(extjsDirPath, os.path.split(dirSrc)[1]), repr(e))
          logging.error(errorMsg)
          raise RuntimeError(errorMsg)
        else:
          logging.error("%s directory already exists. It will be not overwritten!" %
                        os.path.join(extjsDirPath, os.path.split(dirSrc)[1]))

    for filePath in self.__extjsFilesToCopy:
      try:
        shutil.copy(filePath, extjsDirPath)
      except (IOError, OSError) as e:
        errorMsg = "Can not copy %s file to %s: %s" % (filePath, extjsDirPath, repr(e))
        logging.error(errorMsg)

  def __writeINFile(self, tplName, extra=False):
    """
    It creates a temporary file using different templates. For example: /tmp/zmathe/tmp4sibR5.compilejs.app.tpl
    This is required to compile the web framework.

    :params str tplName: it is the name of the template
    :params dict extra: it contains the application location, which will be added to the temporary file
    :return: the location of the file
    """
    inTpl = os.path.join(self.__compileTemplate, tplName)
    with open(inTpl, 'r', encoding="utf-8") as infd:
      data = infd.read()
    data = data.replace("%EXT_VERSION%", self.__extVersion)
    if extra:
      for k in extra:
        data = data.replace("%%%s%%" % k.upper(), extra[k])
    with tempfile.NamedTemporaryFile(suffix=".compilejs.%s" % tplName, delete=False) as fp:
      fp.write(data.encode())
      return fp.name

  def __cmd(self, cmd):
    """
    This is used to execure a command
    :params list cmd: sencha command which will be executed
    """

    env = {}
    for k in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
      if k in os.environ:
        env[k] = os.environ[k]
        os.environ.pop(k)
    logging.info("Command is: %s" % " ".join(cmd))
    try:
      result = subprocess.call(cmd)
    except OSError as e:
      message = 'Command does not exists: %s -> %s' % (','.join(cmd), e)
      logging.error(message)
      raise RuntimeError(message)

    for k in env:
      os.environ[k] = env[k]
    return result

  def __compileApp(self, extPath, extName, appName, extClassPath=""):
    """
    It compiles an application
    :param str extPath: directory full path, which contains the applications
                        for example: /tmp/zmathe/tmpFxr5LzDiracDist/WebAppDIRAC/WebApp/static/DIRA
    :param str extName: the name of the application for example: DIRAC or LHCbDIRAC, etc
    :param str appName: the name of the application for example: Accounting
    :param str extClassPath: if we compile an extension, we can provide the class path of the base class
    """

    inFile = self.__writeINFile("app.tpl", {'APP_LOCATION': '%s.%s.classes.%s' % (extName, appName, appName)})
    buildDir = os.path.join(extPath, appName, 'build')
    try:
      shutil.rmtree(buildDir)
    except OSError:
      pass
    if not os.path.isdir(buildDir):
      try:
        os.makedirs(buildDir)
      except IOError as excp:
        raise RuntimeError("Can't create build dir %s" % excp)
    outFile = os.path.join(buildDir, "index.html")
    compressedJsFile = os.path.join(buildDir, appName + '.js')

    classPath = list(self.__classPaths)
    excludePackage = ",%s.*" % extName
    if extClassPath != "":
      classPath.append(extClassPath)
      excludePackage = ",DIRAC.*,%s.*" % extName

    classPath.append(os.path.join(extPath, appName, "classes"))

    cmd = ['sencha', '-sdk', self.__sdkPath, 'compile', '-classpath=%s' % ",".join(classPath),
           'page', '-name=page', '-input-file', inFile, '-out', outFile, 'and',
           'restore', 'page', 'and', 'exclude', '-not', '-namespace', 'Ext.dirac.*%s' % excludePackage, 'and',
           'concat', '-yui', compressedJsFile]

    if self.__cmd(cmd):
      raise RuntimeError("Error compiling %s.%s" % (extName, appName))

  def __zip(self, staticPath, stack=""):
    """
    It compress the compiled applications
    """
    c = 0
    l = "|/-\\"
    for entry in os.listdir(staticPath):
      n = stack + l[c % len(l)]
      if entry[-3:] == ".gz":
        continue
      ePath = os.path.join(staticPath, entry)
      if os.path.isdir(ePath):
        self.__zip(ePath, n)
        continue
      zipPath = "%s.gz" % ePath
      if os.path.isfile(zipPath):
        if os.stat(zipPath).st_mtime > os.stat(ePath).st_mtime:
          continue
      print("%s%s\r" % (n, " " * (20 - len(n))), end=' ')
      c += 1
      inf = gzip.open(zipPath, "wb", 9)
      with open(ePath, "rb") as outf:
        buf = outf.read(8192)
        while buf:
          inf.write(buf)
          buf = outf.read(8192)
      inf.close()

  def run(self):
    """
    This compiles the web framework
    """
    self.__deployResources()

    # we are compiling an extension of WebAppDIRAC
    # if self.__params.name != 'WebAppDIRAC':
    #   self.__appDependency.update(self.getAppDependencies())
    staticPath = os.path.join(self.__webAppPath, "static")
    logging.info("Compiling core: %s" % staticPath)

    inFile = self.__writeINFile("core.tpl")
    buildDir = os.path.join(staticPath, "core", "build")
    try:
      shutil.rmtree(buildDir)
    except OSError:
      pass
    outFile = os.path.join(staticPath, "core", "build", "index.html")
    logging.info(" IN file written to %s" % inFile)

    cmd = ['sencha', '-sdk', self.__sdkPath, 'compile', '-classpath=%s' % ",".join(self.__classPaths),
           'page', '-yui', '-input-file', inFile, '-out', outFile]

    if self.__cmd(cmd):
      logging.error("Error compiling JS")
      raise RuntimeError("Failed compiling core")

    try:
      os.unlink(inFile)
    except IOError:
      pass
    for staticPath in self.__staticPaths:
      logging.info("Looing into %s" % staticPath)
      extDirectoryContent = os.listdir(staticPath)
      if len(extDirectoryContent) == 0:
        raise RuntimeError("The extension directory is empty:" + str(staticPath))
      else:
        extNames = [ext for ext in extDirectoryContent if 'DIRAC' in ext]
        if len(extNames) > 1:
          extNames.remove('DIRAC')
        extName = extNames[-1]
        logging.info("Detected extension:%s" % extName)

      extPath = os.path.join(staticPath, extName)
      if not os.path.isdir(extPath):
        continue
      logging.info("Exploring %s" % extName)
      for appName in os.listdir(extPath):
        expectedJS = os.path.join(extPath, appName, "classes", "%s.js" % appName)
        if not os.path.isfile(expectedJS):
          continue
        classPath = self.__getClasspath(extName, appName)
        logging.info("Trying to compile %s.%s.classes.%s CLASSPATH=%s" % (extName, appName, appName, classPath))
        self.__compileApp(extPath, extName, appName, classPath)

    logging.info("Zipping static files")
    self.__zip(staticPath)
    logging.info("Done")

  def __getClasspath(self, extName, appName):

    classPath = ''
    dependency = self.__appDependency.get("%s.%s" % (extName, appName), "")

    if dependency != "":
      depPath = dependency.split(".")
      for staticPath in self.__staticPaths:
        expectedJS = os.path.join(staticPath, depPath[0], depPath[1], "classes")
        logging.info(expectedJS)
        if not os.path.isdir(expectedJS):
          continue
        classPath = expectedJS
    return classPath


  # def getAppDependencies(self):
  #   """
  #   Generate the dependency dictionary

  #   :return: Dict
  #   """
  #   if self.__params.name != 'WebAppDIRAC':
  #     self._loadWebAppCFGFiles(self.__params.name)
  #   dependency = {}
  #   fullName = "%s/%s" % ("/WebApp", self.__dependencySection)
  #   optionsList = gConfig.getOptions(fullName)
  #   for opName in optionsList:
  #     opVal = gConfig.getValue("%s/%s" % (fullName, opName))
  #     dependency[opName] = opVal

  #   return dependency

  # def _loadWebAppCFGFiles(self, extension):
  #   """
  #   Load WebApp/web.cfg definitions

  #   :param str extension: the module name of the extension of WebAppDirac for example: LHCbWebDIRAC
  #   """
  #   exts = [extension, "WebAppDIRAC"]
  #   webCFG = CFG()
  #   for modName in reversed(exts):
  #     cfgPath = os.path.join(self.__params.destination, "%s/WebApp" % modName, "web.cfg")
  #     if not os.path.isfile(cfgPath):
  #       logging.info("Web configuration file %s does not exists!" % cfgPath)
  #       continue
  #     try:
  #       modCFG = CFG().loadFromFile(cfgPath)
  #     except Exception as excp:
  #       logging.error("Could not load %s: %s" % (cfgPath, excp))
  #       continue
  #     logging.info("Loaded %s" % cfgPath)
  #     expl = ["/WebApp"]
  #     while len(expl):
  #       current = expl.pop(0)
  #       if not modCFG.isSection(current):
  #         continue
  #       if modCFG.getOption("%s/AbsoluteDefinition" % current, False):
  #         logging.info("%s:%s is an absolute definition" % (modName, current))
  #         try:
  #           webCFG.deleteKey(current)
  #         except Exception:
  #           pass
  #         modCFG.deleteKey("%s/AbsoluteDefinition" % current)
  #       else:
  #         for sec in modCFG[current].listSections():
  #           expl.append("%s/%s" % (current, sec))
  #     # Add the modCFG
  #     webCFG = webCFG.mergeWith(modCFG)
  #   gConfig.loadCFG(webCFG)
