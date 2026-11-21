# AWS Emulator image, based on the official guide:
# https://docs.aws.amazon.com/emulator/latest/userguide/getting-started-docker.html
#
# AWS publishes no prebuilt image, so this downloads the LTS RPM at build time.
# The RPM matching the build platform (x86_64 or aarch64) is picked automatically.

# Download-only stages: the RPM never becomes a layer of the final image.
FROM scratch AS rpm-amd64
ADD https://downloads.aws.com/aws-emulator/packages/aws-emulator/LTS/latest/aws-emulator-x86_64.rpm /aws-emulator.rpm
FROM scratch AS rpm-arm64
ADD https://downloads.aws.com/aws-emulator/packages/aws-emulator/LTS/latest/aws-emulator-aarch64.rpm /aws-emulator.rpm
ARG TARGETARCH
FROM rpm-${TARGETARCH} AS rpm

FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal
RUN --mount=type=bind,from=rpm,source=/aws-emulator.rpm,target=/tmp/aws-emulator.rpm \
    rpm -i /tmp/aws-emulator.rpm \
    && mkdir -p /home/emulator && chown 1000 /home/emulator

USER 1000
ENV HOME=/home/emulator EMULATOR_BIND_ADDRESS=0.0.0.0
ENTRYPOINT ["aws-emulator"]
