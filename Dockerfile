FROM registry.access.redhat.com/ubi9/python-312:1

USER 0
RUN dnf install -y --setopt=install_weak_deps=False \
        bind-utils curl iproute procps-ng util-linux && \
    dnf clean all

WORKDIR /opt/opslab
COPY src ./src
ENV PYTHONPATH=/opt/opslab/src

USER 1001
EXPOSE 8080
CMD ["python", "-m", "opslab.scenarios", "--serve", "8080"]

