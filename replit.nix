{pkgs}: {
  deps = [
    pkgs.zlib
    pkgs.pkg-config
    pkgs.openssl
    pkgs.grpc
    pkgs.c-ares
  ];
}
