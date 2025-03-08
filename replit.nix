{pkgs}: {
  deps = [
    pkgs.lsof
    pkgs.zlib
    pkgs.pkg-config
    pkgs.openssl
    pkgs.grpc
    pkgs.c-ares
  ];
}
