from django.db import models


class Device(models.Model):

    class DeviceType(models.TextChoices):
        WINDOWS = (
            "windows",
            "Windows",
        )

        ANDROID = (
            "android",
            "Android",
        )


    key = models.SlugField(
        max_length=100,
        unique=True,
    )

    name = models.CharField(
        max_length=120,
    )

    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
    )

    hostname = models.CharField(
        max_length=255,
        blank=True,
    )

    manufacturer = models.CharField(
        max_length=120,
        blank=True,
    )

    model = models.CharField(
        max_length=120,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
    )


    def __str__(self):
        return self.name

class SystemMetricSample(models.Model):

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="system_samples",
    )

    timestamp = models.DateTimeField()


    # -------------------------
    # CPU
    # -------------------------

    cpu_percent = models.FloatField()


    # -------------------------
    # Memory
    # -------------------------

    memory_percent = models.FloatField()

    memory_in_use_bytes = (
        models.BigIntegerField()
    )

    memory_available_bytes = (
        models.BigIntegerField()
    )

    pagefile_percent = models.FloatField(
        null=True,
        blank=True,
    )


    # -------------------------
    # Disk
    # -------------------------

    disk_percent = models.FloatField(
        null=True,
        blank=True,
    )

    disk_used_bytes = models.BigIntegerField(
        null=True,
        blank=True,
    )

    disk_free_bytes = models.BigIntegerField(
        null=True,
        blank=True,
    )

    disk_read_bytes_per_second = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )

    disk_write_bytes_per_second = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )


    # -------------------------
    # Network
    # -------------------------

    network_download_bytes_per_second = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )

    network_upload_bytes_per_second = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )


    # -------------------------
    # Processes
    # -------------------------

    process_count = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )


    # -------------------------
    # Lightweight process
    # attribution
    # -------------------------

    top_cpu_process_pid = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )

    top_cpu_process_name = (
        models.CharField(
            max_length=260,
            blank=True,
        )
    )

    top_cpu_process_percent = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )


    top_memory_process_pid = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )

    top_memory_process_name = (
        models.CharField(
            max_length=260,
            blank=True,
        )
    )

    top_memory_process_bytes = (
        models.BigIntegerField(
            null=True,
            blank=True,
        )
    )


    class Meta:
        ordering = [
            "-timestamp",
        ]

        indexes = [
            models.Index(
                fields=[
                    "device",
                    "timestamp",
                ],
                name="telemetry_device_time_idx",
            ),
        ]


    def __str__(self):

        return (
            f"{self.device.name} - "
            f"{self.timestamp}"
        )


class MonitorOverheadSample(models.Model):

    host_device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name=(
            "monitor_overhead_samples"
        ),
    )

    timestamp = models.DateTimeField()


    backend_pid = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )


    cpu_percent = models.FloatField()

    memory_bytes = models.BigIntegerField()

    memory_percent = models.FloatField()


    read_bytes_per_second = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )

    write_bytes_per_second = (
        models.FloatField(
            null=True,
            blank=True,
        )
    )


    sample_duration_ms = (
        models.FloatField()
    )


    thread_count = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )

    handle_count = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )

    network_socket_count = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
        )
    )


    class Meta:
        ordering = [
            "-timestamp",
        ]

        indexes = [
            models.Index(
                fields=[
                    "host_device",
                    "timestamp",
                ],
                name="overhead_device_time_idx",
            ),
        ]


    def __str__(self):

        return (
            f"Sys Monitor overhead - "
            f"{self.timestamp}"
        )