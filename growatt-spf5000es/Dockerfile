ARG BUILD_FROM
ARG BUILD_ARCH
ARG BUILD_VERSION
ARG BUILD_REVISION=48d262c847c5e35ebe824fed08dd6fc0b483c6bd

FROM golang:1.26-alpine AS builder

ARG BUILD_ARCH=amd64
ARG BUILD_REVISION=48d262c847c5e35ebe824fed08dd6fc0b483c6bd

WORKDIR /src
COPY server/ .

RUN go test ./...

RUN case "${BUILD_ARCH}" in \
      aarch64) export GOARCH=arm64 ;; \
      amd64) export GOARCH=amd64 ;; \
      *) echo "unsupported BUILD_ARCH: ${BUILD_ARCH}" >&2; exit 1 ;; \
    esac && \
    CGO_ENABLED=0 GOOS=linux \
    go build -trimpath \
    -ldflags "-s -w -X main.buildRevision=${BUILD_REVISION}" \
    -o /spf5000es-server .

FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH
ARG BUILD_REVISION=48d262c847c5e35ebe824fed08dd6fc0b483c6bd

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/matiebird/home-assistant-addons" \
  org.opencontainers.image.revision="${BUILD_REVISION}"

RUN apk add --no-cache python3

COPY --from=builder /spf5000es-server /usr/local/bin/spf5000es-server
COPY run.sh render_config.py /
RUN chmod a+x /run.sh

WORKDIR /data

CMD ["/run.sh"]
