{
  description = "pypulseq-issues: development shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShellNoCC (
          {
            packages = [
              pkgs.python312
              pkgs.uv
              pkgs.ruff
              pkgs.octave
              pkgs.gh
              pkgs.git
              pkgs.jq
              pkgs.shellcheck
            ];
            # uv runs the examples on the Nix python and never downloads one.
            UV_PYTHON = "${pkgs.python312}/bin/python3";
            UV_PYTHON_DOWNLOADS = "never";
            # MATLAB Pulseq for the repro.m examples, pinned to the commit that the
            # notes name: octave --eval "addpath('$MATLAB_PULSEQ/matlab'); run('<repro.m>')"
            MATLAB_PULSEQ = pkgs.fetchFromGitHub {
              owner = "pulseq";
              repo = "pulseq";
              rev = "c7469123c2f381f065986e6cc3a7d09730ed16ef";
              hash = "sha256-Q9XjlghUUVDb9ZLs6UQoh6Q/n+KhrrVlyhcIsVzuuig=";
            };
            MATLAB_PULSEQ_REV = "c7469123c2f381f065986e6cc3a7d09730ed16ef";
          }
          // pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
            # PyPI manylinux wheels (numpy) load libstdc++ and zlib, which the
            # Nix python does not have on its library path.
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
            ];
          }
        );
      });
    };
}
