from conans import ConanFile, CMake, tools
from conans.tools import download
from conans.tools import unzip
from multiprocessing import cpu_count
import os


class LibsbmlConan(ConanFile):
    name = "libsbml"
    version = "5.13.0"
    license = "http://sbml.org/Software/libSBML/LibSBML_License"
    url="http://github.com/eliaskousk/conan-libsbml"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fpic": [True, False], "packages": [True, False]}
    default_options = "shared=False", "fpic=True", "packages=False"
    generators = "cmake"
    zip_folder_name = "libsbml-%s" % version

    def config_options(self):
        self.requires("libxml2/2.9.4@eliaskousk/stable")
        self.options['libxml2'].shared = self.options.shared

        self.requires("libiconv/1.14@eliaskousk/stable")
        self.options['libiconv'].shared = self.options.shared

        self.requires("zlib/1.2.9@lasote/stable")
        self.options['zlib'].shared = self.options.shared

        self.requires("bzip2/1.0.6@lasote/stable")
        self.options['bzip2'].shared = self.options.shared

    def source(self):
        packages = "-plus-packages" if self.options.packages else ""
        zip_name = "libSBML-%s-core%s-src.tar.gz" % (self.version, packages)
        url = "https://netcologne.dl.sourceforge.net/project/sbml/libsbml/5.13.0/stable/%s" % zip_name
        download(url, zip_name)
        unzip(zip_name)
        os.unlink(zip_name)

        # This small hack might be useful to guarantee proper settings
        # if the packaged project doesn't have variables to set them properly
        cmakelists_path = os.path.join(self.zip_folder_name, "CMakeLists.txt")
        print cmakelists_path
        tools.replace_in_file(cmakelists_path, "project(libsbml)", '''project(libsbml)
include(${CMAKE_BINARY_DIR}/../conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        cmake = CMake(self.settings)

        if self.settings.os == "Windows":
            self.run("IF not exist _build mkdir _build")
        else:
            self.run("mkdir _build")

        cd_build = "cd _build"
        shared = "-DBUILD_SHARED_LIBS=ON" if self.options.shared else ""
        fpic = "-DCMAKE_POSITION_INDEPENDENT_CODE=TRUE" if self.options.fpic else ""

        print cmake.command_line

        self.run("%s && cmake ../%s %s %s %s" % (cd_build, self.zip_folder_name,
                                                 cmake.command_line, shared, fpic))
        self.run("%s && cmake --build . %s -- -j%s" % (cd_build, cmake.build_config, cpu_count()))

    def package(self):
        # Copying headers
        incdir = "%s/src/sbml" % self.zip_folder_name
        self.copy(pattern="*.h", dst="include/sbml", src=incdir, keep_path=True)

        if self.options.shared:
            # Copying dynamic libs
            libdir = "_build/src"
            self.copy(pattern="*.so*", dst="lib", src=libdir, keep_path=False)
            self.copy(pattern="*.dylib*", dst="lib", src=libdir, keep_path=False)
            self.copy(pattern="*.dll", dst="bin", src=libdir, keep_path=False)
        else:
            # Copying static libs
            libdir = "_build/lib"
            self.copy(pattern="*.a", dst="lib", src=libdir, keep_path=False)

        self.copy(pattern="*.lib", dst="lib", src=libdir, keep_path=False)

    def package_info(self):
        libfile = "libsbml"
        if not self.settings.os == "Windows":
            if self.options.shared:
                if self.settings.os == "Linux":
                    libfile += ".so"
                if self.settings.os == "Macos":
                    libfile += ".dylib"
            else:
                libfile += "-static.a"
        else:
            if self.options.shared:
                libfile += ".dll"
            else:
                libfile += "-static.lib"

        self.cpp_info.libs = [libfile]
