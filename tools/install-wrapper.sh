#!/usr/bin/env sh
set -eu
# Optional bootstrap, using the official Apache Maven Wrapper plugin.
# Review and commit the generated scripts and checksum configuration separately.
exec mvn org.apache.maven.plugins:maven-wrapper-plugin:3.3.4:wrapper -Dmaven=3.9.11 -Dtype=only-script
