from conan.packager import ConanMultiPackager
import platform


if __name__ == "__main__":
    builder = ConanMultiPackager(username="eliaskousk")

    builder.add_common_builds(shared_option_name="libsbml:shared", pure_c=False)

    if platform.system() == "Darwin":
        filtered_builds = []
        for settings, options in builder.builds:
            # Some isues with OSx and x86 with libxml2 (link with iconv),
            if settings["arch"] != "x86":
                filtered_builds.append([settings, options])
        builder.builds = filtered_builds

    builder.run()

