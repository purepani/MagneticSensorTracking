{
  inputs,
  cell,
}: {
  magneticsensortracking = {
    config,
    lib,
    dream2nix,
    ...
  }: {
    imports = [
      #      inputs.dream2nix.modules.dream2nix.core
      inputs.dream2nix.modules.dream2nix.WIP-python-pdm
    ];

    deps = {python, ...}: {
      python3 = python;
    };

    pdm = {
      lockfile = "${inputs.self}/pdm.lock";
      pyproject = "${inputs.self}/pyproject.toml";
      pythonInterpreter = config.deps.python3;
    };
    groups.main = {
      packages.magneticsensortracking = {
        name = "magneticsensortracking";
        version = "0.1.0";
        imports = [
          dream2nix.modules.dream2nix.buildPythonPackage
          dream2nix.modules.dream2nix.mkDerivation
          dream2nix.modules.dream2nix.package-func
        ];
        buildPythonPackage = {
          format = "pyproject";
        };
        mkDerivation = {
          # required: { pname, file, version, hash, kind, curlOpts ? "" }:
          src = "${inputs.self}";
          propagatedBuildInputs = lib.attrsets.attrValues config.groups.default.public.packages ++ [config.deps.python3.pkgs.pdm-backend];
        };
      };
    };
  };
}
