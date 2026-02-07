# Installation Colima MacOS

# Colima mit Profile starten

colima start --profile m1-native \
  --cpu 4 \
  --memory 6 \
  --disk 100 \
  --arch aarch64 \
  --vm-type vz \
  --dns 1.1.1.1 \
  --dns 8.8.8.8 \
  --mount-type virtiofs

# Später einfach:
colima start --profile m1-native


# Network
docker network create thwelly-net
