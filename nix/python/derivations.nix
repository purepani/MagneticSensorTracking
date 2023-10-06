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
      inputs.dream2nix.modules.dream2nix.WIP-python-pdm
    ];
    pdm = {
      lockfile = "${inputs.self}/pdm.lock";
      pyproject = "${inputs.self}/pyproject.toml";
      pythonInterpreter = inputs.nixpkgs.python3;
    };
  };
}
