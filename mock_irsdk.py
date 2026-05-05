class MockIRSDK:
    """Minimal irsdk.IRSDK stand-in for test mode."""

    def startup(self):
        return True

    def shutdown(self):
        pass

    @property
    def is_connected(self) -> bool:
        return True

    def freeze_var_buffer_latest(self):
        pass

    def unfreeze_var_buffer_latest(self):
        pass

    def __getitem__(self, key):
        return 0
