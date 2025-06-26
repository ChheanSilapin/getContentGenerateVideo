# Custom Filename Features - Complete Implementation

## 🎯 Overview

Your video generator now has comprehensive custom filename support for both **individual** and **group** generation in both **image** and **video** tabs!

## ✅ Features Implemented

### **1. Individual Entry Custom Filenames**

#### **Image Tab - Individual Images**
- ✅ Custom filename input field for each image entry
- ✅ Placeholder text: "Enter custom filename (optional)"
- ✅ Automatic .mp4 extension
- ✅ Real-time filename validation
- ✅ Fallback to default naming if empty

#### **Video Tab - Individual Videos**
- ✅ Custom filename input field for each video entry
- ✅ Same UI design as image tab for consistency
- ✅ Integrated with existing video processing workflow
- ✅ Supports all video processing features

### **2. Group Entry Custom Filenames**

#### **Group Output Filename**
- ✅ Custom filename for the final combined group video
- ✅ Shows default name in gray text as reference
- ✅ Applied to the merged/combined output file
- ✅ Works for both image and video group generation

#### **Individual Videos Within Groups**
- ✅ Custom filename for each individual video before combining
- ✅ Visible when group details are expanded (🔽 button)
- ✅ Each video in the group can have its own custom name
- ✅ Applied before videos are merged into final group output

### **3. Filename Validation & Safety**

#### **Automatic Sanitization**
- ✅ Invalid characters (`<>:"/\|?*`) replaced with underscores
- ✅ Reserved Windows names (CON, PRN, etc.) handled
- ✅ Length limits enforced (255 characters)
- ✅ Leading/trailing spaces and dots removed

#### **Real-time Validation**
- ✅ Validates as you type
- ✅ Visual feedback for invalid characters
- ✅ Automatic cleanup suggestions
- ✅ Prevents file system errors

## 🎮 How to Use

### **Individual Entries**

1. **Add an image or video entry**
2. **Find the "📝 Custom Filename:" field** (appears inline with file path)
3. **Enter your desired filename** (without .mp4 extension)
4. **Leave blank** to use default naming
5. **Generate** - your custom filename will be used!

### **Group Entries**

1. **Create or load a group** (multiple videos/images)
2. **Group filename**: Enter custom name in the main group section
3. **Individual filenames**: 
   - Click the **🔽 expand button** to show group details
   - Each video will have its own "📝 Individual Filename:" field
   - Enter custom names for individual videos (optional)
4. **Generate** - both group and individual custom names will be used!

## 📋 UI Layout

### **Individual Entry Layout**
```
📁 File: /path/to/video.mp4    📝 Custom Filename: [my_custom_name] .mp4
💬 Prompt: [Your text here...]
```

### **Group Entry Layout**
```
📦 Group: My Group (3 videos)
📁 Output: (My Group)
📝 Custom Filename: [my_group_output] .mp4
🎥 Videos: video1.mp4, video2.mp4, video3.mp4    🔽 ✕

[When expanded 🔼]
─────────────────────────────────────────────────
🎬 Video 1: video1.mp4
📁 File: /path/to/video1.mp4
💬 Prompt: [First video prompt...]
📝 Individual Filename: [custom_video_1] .mp4

🎬 Video 2: video2.mp4
📁 File: /path/to/video2.mp4  
💬 Prompt: [Second video prompt...]
📝 Individual Filename: [custom_video_2] .mp4
```

## 🔧 Technical Implementation

### **File Structure**
- `ui/components/image_entry.py` - Individual image custom filenames
- `ui/components/video_entry.py` - Individual video custom filenames  
- `ui/components/group_entry.py` - Group and individual-within-group custom filenames
- `utils/filename_validator.py` - Validation and sanitization logic
- `models/batch_processor.py` - Processing integration
- `models/video_processor.py` - Video generation integration

### **Data Flow**
1. **UI Input** → Custom filename entered in text field
2. **Validation** → Real-time validation and sanitization
3. **Data Collection** → Filename included in entry data
4. **Batch Processing** → Custom filename passed to processors
5. **Video Generation** → Custom filename applied to output file
6. **Final Output** → Video saved with custom name + timestamp

### **Filename Processing**
```python
# Individual entries
entry_data = {
    "video_file": "input.mp4",
    "prompt": "My prompt",
    "custom_filename": "my_custom_video"  # → my_custom_video.mp4
}

# Group entries  
group_data = {
    "output_name": "my_group_output.mp4",  # Group custom filename
    "pairs": [
        {
            "video_file": "video1.mp4",
            "prompt": "Prompt 1", 
            "custom_filename": "custom_video_1"  # Individual custom filename
        }
    ]
}
```

## 🎉 Benefits

### **Organization**
- ✅ **Meaningful names** instead of timestamps
- ✅ **Project-specific naming** for better file management
- ✅ **Consistent naming conventions** across your videos

### **Workflow**
- ✅ **Batch processing** with custom names
- ✅ **Group organization** with both group and individual naming
- ✅ **No filename conflicts** (automatic timestamp addition)

### **User Experience**
- ✅ **Optional feature** - works with or without custom names
- ✅ **Consistent UI** across image and video tabs
- ✅ **Real-time validation** prevents errors
- ✅ **Placeholder text** guides usage

## 🧪 Testing

Run the test suite to verify functionality:
```bash
python test_custom_filenames.py
```

**Expected output:**
- ✅ Filename validator tests
- ✅ Individual entry data tests  
- ✅ Group entry data tests
- ✅ UI component import tests
- ✅ Batch processor integration tests

## 📝 Examples

### **Individual Video Example**
- **Input**: Custom filename = "my_presentation_video"
- **Output**: `my_presentation_video_20241224_143022.mp4`

### **Group Video Example**
- **Group custom filename**: "complete_tutorial_series"
- **Individual videos**: "intro_video", "main_content", "conclusion"
- **Final output**: `complete_tutorial_series_20241224_143022.mp4`
- **Individual outputs** (before merging): 
  - `intro_video_20241224_143022.mp4`
  - `main_content_20241224_143023.mp4` 
  - `conclusion_20241224_143024.mp4`

## 🚀 Ready to Use!

Your video generator now has complete custom filename support! The feature is:
- ✅ **Fully integrated** with existing workflows
- ✅ **Backward compatible** - existing functionality unchanged
- ✅ **User-friendly** with intuitive UI
- ✅ **Robust** with comprehensive validation
- ✅ **Tested** and verified working

**Start using custom filenames today for better video organization!** 🎬
