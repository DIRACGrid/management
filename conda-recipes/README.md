# DIRACGrid's Conda recipes

This directory contains the recipes that are used to generate the packages on the [`diracgrid`](https://anaconda.org/diracgrid/) conda channel.
This should only be used in situations where it is impractical to add packages to [conda-forge](https://conda-forge.org/) directly.
New packages can be added to conda-forge using [`staged-recipes`](https://github.com/conda-forge/staged-recipes/) and existing packages can be modified by making a PR to the corresponding [`feedstock`](https://conda-forge.org/feedstocks/).

If it is absolutely essential for DIRAC to have a custom build of a package, a new directory can be added here. An reference for the `meta.yaml` syntax can be found [here](https://conda.io/projects/conda-build/en/latest/resources/define-metadata.html) and the [conda-forge](https://conda-forge.org/feedstocks/) is a good source of examples. You can then test building packages by running:

```bash
conda build -c diracgrid -c conda-forge -m conda_build_config.yaml my-package/
```

The `extra-packages/conda_build_config.yaml` file is a "[variant config file](https://conda.io/projects/conda-build/en/latest/resources/variants.html#creating-conda-build-variant-config-files)" which is used to constrain the versions of dependencies. Currently this is only used to set the Python interpreter version. If shared library dependencies are added, new values should be added based on the main [conda-forge configuration](https://github.com/conda-forge/conda-forge-pinning-feedstock/blob/master/recipe/conda_build_config.yaml).

## Packages

### tornado

**Reason for not using conda-forge:** This package is distributed using DIRACGrid's channel as it is a fork of the main upstream package, making it ineligible for conda-forge.

**Version history:**
* `5.1.1+dirac.1-0` Initial release

### tornado_m2crypto

**Reason for not using conda-forge:** This package is completely non-functional without DIRACGrid's fork of tornado.

**Version history:**
* `0.1.1-0` Initial release
