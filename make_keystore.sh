#!/usr/bin/env bash
set -euo pipefail

KEYSTORE="${1:-signingkey.jks}"
ALIAS="${2:-sheep-manga}"

echo "建立 $KEYSTORE"
echo "請記住 store password 與 key password；之後每次發布都必須用同一把金鑰。"

keytool -genkeypair \
  -v \
  -keystore "$KEYSTORE" \
  -alias "$ALIAS" \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -dname "CN=Sheep Manga, OU=Extensions, O=Sheep Manga, L=Taiwan, C=TW"

echo
echo "SHA-256 fingerprint："
keytool -list -v -keystore "$KEYSTORE" -alias "$ALIAS" | grep -i "SHA256"
echo
echo "Base64（貼到 GitHub Secret KEYSTORE_B64）："
base64 < "$KEYSTORE" | tr -d '\n'
echo
