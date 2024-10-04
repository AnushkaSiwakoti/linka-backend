

# # ARG PYTHON_VERSION=3.12.2
# # FROM python:${PYTHON_VERSION}-slim as base

# # # Prevents Python from writing pyc files.
# # ENV PYTHONDONTWRITEBYTECODE=1

# # # Keeps Python from buffering stdout and stderr.
# # ENV PYTHONUNBUFFERED=1

# # WORKDIR /usr/src/app

# # # Install system dependencies required for GDAL
# # USER root
# # RUN apt-get update && apt-get install -y \
# #     libgdal-dev \
# #     gcc \
# #     g++ \
# #     && rm -rf /var/lib/apt/lists/*

# # # Determine GDAL version and set as environment variable
# # RUN GDAL_VERSION=$(gdal-config --version) && \
# #     echo "GDAL version is $GDAL_VERSION" && \
# #     echo "GDAL_VERSION=$GDAL_VERSION" >> /etc/environment && \
# #     echo "GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.$GDAL_VERSION" >> /etc/environment && \
# #     echo "GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so" >> /etc/environment

# # # Now set the ENV variables to ensure they persist
# # ENV GDAL_VERSION=$GDAL_VERSION
# # ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.$GDAL_VERSION
# # ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# # # Install Python packages as root
# # RUN --mount=type=cache,target=/root/.cache/pip \
# #     --mount=type=bind,source=requirements.txt,target=requirements.txt,readonly \
# #     pip install -r requirements.txt

# # # Create a non-privileged user to run the application.
# # ARG UID=10001
# # RUN adduser \
# #     --disabled-password \
# #     --gecos "" \
# #     --home "/nonexistent" \
# #     --shell "/sbin/nologin" \
# #     --no-create-home \
# #     --uid "${UID}" \
# #     appuser

# # # Switch back to the non-privileged user for the rest of the setup
# # USER appuser

# # # Copy the source code into the container.
# # COPY --chown=appuser:appuser . .

# # # Expose the port that the application listens on.
# # EXPOSE 8000

# # # Run the application.
# # CMD python manage.py runserver 0.0.0.0:8000

# # syntax=docker/dockerfile:1

# ARG PYTHON_VERSION=3.12.2
# FROM python:${PYTHON_VERSION}-slim as base

# # Prevents Python from writing pyc files.
# ENV PYTHONDONTWRITEBYTECODE=1

# # Keeps Python from buffering stdout and stderr.
# ENV PYTHONUNBUFFERED=1

# # Set working directory
# WORKDIR /usr/src/app

# # Install system dependencies required for GDAL and cryptography
# USER root
# RUN apt-get update && apt-get install -y \
#     libgdal-dev \
#     gcc \
#     g++ \
#     libssl-dev \
#     libffi-dev \
#     python3-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Determine GDAL version and set as environment variable
# RUN GDAL_VERSION=$(gdal-config --version) && \
#     echo "GDAL version is $GDAL_VERSION" && \
#     echo "GDAL_VERSION=$GDAL_VERSION" >> /etc/environment && \
#     echo "GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.$GDAL_VERSION" >> /etc/environment && \
#     echo "GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so" >> /etc/environment

# # Set GDAL ENV variables
# ENV GDAL_VERSION=$GDAL_VERSION
# ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.$GDAL_VERSION
# ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# # Copy the requirements file and install Python packages
# COPY requirements.txt .
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install -r requirements.txt

# # Create a non-privileged user to run the application.
# ARG UID=10001
# RUN adduser \
#     --disabled-password \
#     --gecos "" \
#     --home "/nonexistent" \
#     --shell "/sbin/nologin" \
#     --no-create-home \
#     --uid "${UID}" \
#     appuser

# # Switch to the non-privileged user
# USER appuser

# # Copy the source code into the container
# COPY --chown=appuser:appuser . .

# # Expose the port that the application listens on
# EXPOSE 8000

# # Run the application
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# syntax=docker/dockerfile:1

# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.2
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr.
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /usr/src/app

# Install system dependencies required for GDAL, cryptography, and other packages
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libgdal-dev \
    gcc \
    g++ \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Determine GDAL version and set as environment variable
RUN GDAL_VERSION=$(gdal-config --version) && \
    echo "GDAL version is $GDAL_VERSION" && \
    echo "GDAL_VERSION=$GDAL_VERSION" >> /etc/environment && \
    echo "GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.$GDAL_VERSION" >> /etc/environment && \
    echo "GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so" >> /etc/environment

# Set GDAL ENV variables
ENV GDAL_VERSION=$GDAL_VERSION
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.$GDAL_VERSION
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Copy requirements file and install Python packages
COPY requirements.txt .

# Install pip dependencies as root
RUN pip install --no-cache-dir -r requirements.txt --use-pep517

# Download and manually install cryptography if pip install fails
RUN wget https://files.pythonhosted.org/packages/7b/2e/469af8e5c7c8d0de99eb83c0f5c27394b7715e226bd90b06ddc2db8ddcd1/cryptography-43.0.1-cp312-cp312-manylinux_2_28_x86_64.whl && \
    pip install cryptography-43.0.1-cp312-cp312-manylinux_2_28_x86_64.whl

# Create a non-privileged user to run the application
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Switch to the non-privileged user
USER appuser

# Copy the source code into the container
COPY --chown=appuser:appuser . .

# Set the home directory for appuser
ENV HOME=/home/appuser

# Expose the port that the application listens on
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

