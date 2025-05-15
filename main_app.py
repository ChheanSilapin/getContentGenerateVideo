#!/usr/bin/env python3
"""
Main application file that connects the UI with the application logic
"""
# Apply MoviePy patch first
import moviepy_patch

import sys
import os
import threading
import datetime
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QMetaObject, Signal, Slot, QObject

# Import the UI class
from ui.ui_dialog import Ui_dialog

# Import the model
from models.video_generator import VideoGeneratorModel

# Create a signal class for thread-safe UI updates
class UpdateSignals(QObject):
    update_progress = Signal(int)
    update_log = Signal(str)
    show_message = Signal(str, str, bool)  # title, message, is_error
    reset_buttons = Signal()

class VideoGeneratorApp(QDialog):
    """Main application class that connects UI with logic"""

    def __init__(self):
        super().__init__()

        # Set up the UI
        self.ui = Ui_dialog()
        self.ui.setupUi(self)

        # Create the model
        self.model = VideoGeneratorModel()

        # Create signals for thread-safe UI updates
        self.signals = UpdateSignals()
        self.signals.update_progress.connect(self._update_progress)
        self.signals.update_log.connect(self._update_log)
        self.signals.show_message.connect(self._show_message)
        self.signals.reset_buttons.connect(self._reset_buttons)

        # Connect UI signals to slots
        self.setup_connections()

        # Thread control
        self.generation_thread = None
        self.stop_event = None

        # Store the last output folder
        self.last_output_folder = None

    def setup_connections(self):
        """Connect UI elements to their functions"""
        # Connect buttons
        self.ui.btnUrl.clicked.connect(self.handle_website_url)
        self.ui.btnFolder.clicked.connect(self.browse_local_folder)
        self.ui.btnStart.clicked.connect(self.start_generation)
        self.ui.btnStop.clicked.connect(self.stop_generation)
        self.ui.btnClear.clicked.connect(self.clear_inputs)
        self.ui.btnClean.clicked.connect(self.clear_images)

    def handle_website_url(self):
        """Handle website URL button click"""
        # Get the URL from the text field
        url = self.ui.txtUrl.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a website URL")
            return

        # You could validate the URL here
        # For now, just acknowledge it
        QMessageBox.information(self, "URL Set", f"Website URL set to: {url}")

    def browse_local_folder(self):
        """Open folder browser dialog"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder Containing Images")
        if folder_path:
            self.ui.lineEdit_local_folder.setText(folder_path)

            # Switch to the Image tab
            self.ui.tabWidget.setCurrentIndex(1)

            # Here you would load images from the folder
            # For now, just show a message
            self.ui.lineEdit_select_image.setText(f"Images from: {folder_path}")

    def clear_images(self):
        """Clear selected images"""
        self.ui.lineEdit_select_image.clear()
        QMessageBox.information(self, "Images Cleared", "All selected images have been cleared")

    def clear_inputs(self):
        """Clear all input fields"""
        self.ui.txtPrompt.clear()
        self.ui.txtUrl.clear()
        self.ui.lineEdit_local_folder.clear()
        self.ui.progressBar_converting.setValue(0)

    def start_generation(self):
        """Start the video generation process"""
        # Get text input
        text_input = self.ui.txtPrompt.text().strip()
        if not text_input:
            QMessageBox.warning(self, "Input Error", "Please enter text for voice generation")
            return

        # Get image source
        website_url = self.ui.txtUrl.text().strip()
        local_folder = self.ui.lineEdit_local_folder.text().strip()

        if not website_url and not local_folder and not self.model.selected_images:
            QMessageBox.warning(self, "Input Error", "Please provide either a website URL or a local folder, or select images")
            return

        # If website URL is provided but no images are selected, prompt user to preview first
        if website_url and not self.model.selected_images:
            reply = QMessageBox.question(
                self,
                "Preview Images",
                "Would you like to preview and select images from the website before generating?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                # Call the preview function
                self.preview_images_from_url()
                return

        # Determine image source
        if self.model.selected_images:
            image_source = "3"  # Selected images
        elif website_url:
            image_source = "1"  # Website URL
        else:
            image_source = "2"  # Local folder

        # Get processing option (CPU/GPU)
        processing_option = "gpu" if self.ui.cbCpuGpu.currentText() == "GPU" else "cpu"

        # Update model with user inputs
        self.model.text_input = text_input
        self.model.image_source = image_source
        self.model.website_url = website_url
        self.model.local_folder = local_folder
        self.model.processing_option = processing_option

        # Create output directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", f"video_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        self.model.output_folder = output_dir

        # Reset progress bar
        self.ui.progressBar_converting.setValue(0)

        # Create a stop event for the thread
        self.stop_event = threading.Event()

        # Start the generation thread
        self.worker = VideoGenerationWorker(self.model, self.stop_event)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.finished.connect(self.generation_finished)
        self.worker.signals.error.connect(self.generation_error)
        self.worker.signals.update_log.connect(self.update_log)
        self.worker.signals.reset_buttons.connect(self.reset_buttons)
        self.worker.signals.show_message.connect(self.show_message)

        # Start the thread
        self.threadpool.start(self.worker)

        # Update UI
        self.ui.btnGenerate.setEnabled(False)
        self.ui.btnStop.setEnabled(True)
        self.ui.progressBar_converting.setValue(10)
        self.ui.txtLog.append("Starting video generation process...")

    def preview_images_from_url(self):
        """Preview images from URL before generating video"""
        url = self.ui.txtUrl.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a website URL")
            return

        # Show progress dialog
        progress_dialog = QProgressDialog("Downloading images for preview...", "Cancel", 0, 100, self)
        progress_dialog.setWindowTitle("Downloading Images")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(10)

        # Create a worker for downloading images
        preview_worker = ImagePreviewWorker(self.model, url)
        preview_worker.signals.progress.connect(progress_dialog.setValue)
        preview_worker.signals.finished.connect(lambda image_paths: self.show_image_selection(image_paths, progress_dialog))
        preview_worker.signals.error.connect(lambda error: self.handle_preview_error(error, progress_dialog))

        # Start the worker
        self.threadpool.start(preview_worker)

    def show_image_selection(self, image_paths, progress_dialog=None):
        """Show image selection dialog"""
        # Close progress dialog
        if progress_dialog:
            progress_dialog.close()

        if not image_paths:
            QMessageBox.warning(self, "Preview Error", "No images found at the URL")
            return

        # Create image selection dialog
        selection_dialog = QDialog(self)
        selection_dialog.setWindowTitle("Select Images")
        selection_dialog.setMinimumSize(800, 600)

        # Create layout
        layout = QVBoxLayout(selection_dialog)

        # Create scroll area for images
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Create checkboxes for each image
        checkboxes = []
        for img_path in image_paths:
            img_frame = QFrame()
            img_layout = QHBoxLayout(img_frame)

            # Create checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Default to selected
            checkbox.img_path = img_path
            checkboxes.append(checkbox)
            img_layout.addWidget(checkbox)

            # Create image thumbnail
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label = QLabel()
                img_label.setPixmap(pixmap)
                img_layout.addWidget(img_label)

            # Add filename
            name_label = QLabel(os.path.basename(img_path))
            img_layout.addWidget(name_label)

            # Add spacer
            img_layout.addStretch()

            # Add to scroll layout
            scroll_layout.addWidget(img_frame)

        # Add a spacer at the end
        scroll_layout.addStretch()

        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Add buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes])
        button_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes])
        button_layout.addWidget(deselect_all_btn)

        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(selection_dialog.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(selection_dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Show dialog
        if selection_dialog.exec_() == QDialog.Accepted:
            # Get selected images
            selected_images = [cb.img_path for cb in checkboxes if cb.isChecked()]

            if selected_images:
                # Update model with selected images
                self.model.selected_images = selected_images
                QMessageBox.information(self, "Images Selected", f"Selected {len(selected_images)} images for video generation")

                # Start generation automatically
                self.start_generation()
            else:
                QMessageBox.warning(self, "No Images", "No images selected. Please select at least one image.")
        else:
            # User cancelled
            pass

    def handle_preview_error(self, error, progress_dialog=None):
        """Handle errors during image preview"""
        if progress_dialog:
            progress_dialog.close()

        QMessageBox.critical(self, "Preview Error", f"Error downloading images: {error}")

    def run_generation(self):
        """Run the video generation process in a thread"""
        try:
            # Redirect stdout to capture output
            import io
            import sys
            original_stdout = sys.stdout

            class LogRedirector:
                def __init__(self, signal):
                    self.signal = signal
                    self.buffer = ""

                def write(self, text):
                    self.buffer += text
                    if text.endswith('\n'):
                        self.signal.emit(self.buffer)
                        self.buffer = ""

                def flush(self):
                    if self.buffer:
                        self.signal.emit(self.buffer)
                        self.buffer = ""

            sys.stdout = LogRedirector(self.signals.update_log)

            # Generate the video
            subtitlePath, videoPath, output_dir = self.model.generate_video(self.stop_event)

            # Store the output directory
            if output_dir and os.path.exists(output_dir):
                self.last_output_folder = output_dir

            # Check if we were stopped
            if self.stop_event and self.stop_event.is_set():
                print("Generation stopped by user")
                self.signals.reset_buttons.emit()
                return

            # Finalize the video
            if subtitlePath and videoPath and output_dir:
                result = self.model.finalize_video(subtitlePath, videoPath, output_dir, self.stop_event)
                if result:
                    print(f"Video generated successfully: {os.path.basename(result)}")
                    self.signals.show_message.emit("Success", f"Video generated successfully: {os.path.basename(result)}", False)
                else:
                    print("Failed to finalize video")
                    self.signals.show_message.emit("Error", "Failed to finalize video", True)
            else:
                print("Video generation failed")
                self.signals.show_message.emit("Error", "Video generation failed", True)

        except Exception as error:
            import traceback
            print(f"\nERROR in generation thread: {error}")
            traceback.print_exc()
            self.signals.show_message.emit("Error", f"An error occurred: {error}", True)

        finally:
            # Restore stdout
            sys.stdout = original_stdout

            # Reset buttons
            self.signals.reset_buttons.emit()

    @Slot()
    def _reset_buttons(self):
        """Reset button states"""
        self.ui.btnStart.setEnabled(True)
        self.ui.btnStop.setEnabled(False)

    @Slot(int)
    def _update_progress(self, value):
        """Update progress bar"""
        self.ui.progressBar_converting.setValue(value)

    @Slot(str)
    def _update_log(self, text):
        """Update log text"""
        current_text = self.ui.lineEdit_log.text()
        # Append the new text to the current text
        self.ui.lineEdit_log.setText(current_text + text)

    @Slot(str, str, bool)
    def _show_message(self, title, message, is_error):
        """Show a message box"""
        if is_error:
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)

    def stop_generation(self):
        """Stop the video generation process"""
        if self.stop_event:
            self.stop_event.set()
            print("Stopping generation...")

# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoGeneratorApp()
    window.show()
    sys.exit(app.exec())



