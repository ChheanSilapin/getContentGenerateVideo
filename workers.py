class ImagePreviewWorker(QRunnable):
    """Worker thread for downloading images for preview"""
    
    def __init__(self, model, url):
        super().__init__()
        self.model = model
        self.url = url
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        """Download images for preview"""
        try:
            # Update progress
            self.signals.progress.emit(10)
            
            # Download images
            image_paths = self.model.preview_images_from_url(self.url)
            
            # Update progress
            self.signals.progress.emit(100)
            
            # Emit result
            self.signals.finished.emit(image_paths)
        except Exception as e:
            # Handle errors
            self.signals.error.emit(str(e))