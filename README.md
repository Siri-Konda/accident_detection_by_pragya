# PRAGYA
 VISION BASED AUTOMATIC DETECTION OF ACCIDENTS IN HIGHWAY


## 1. Planning

### Stage 1: Brainstorming Ideas

- Using Yolo for object detection and experimenting with value, camera warps, physics and pixels to detect crashes
- Using Clip to detect crashes for static images
- Alert could contain severity level (Detecting blood, smoke or fire), possibly extract emergency contact using the number plate (Can be detected using YOLO), number of people involved in the accidents(so that the required number of ambulances can be sent)
- Can (store and) display the clip of the accident footage
- Generate required SMS/ automated Call After (or otherwise) human approval (10-20 sec window per detection)
- detect the number plate using ALDR/OCR and extract text after resizing (adjusting for the camera warp)
- Detect kidnappings
- Raising tickets for "speed limit exceeded" cases
- Saving a map (data) of camera ID with the nearest police station/ Hospital to ensure effectiveness


### Stage 2: Picking out essential ideas 

![planning_2.jpeg](/pragya_readme/planning_2.jpeg)

![planning_1.jpeg](/pragya_readme/planning_1.jpeg)

## 2. Architecture

  ### Client - server architecture (simplified)

  <img width="1346" height="1600" alt="image" src="https://github.com/user-attachments/assets/e4c3aa12-f49b-4c18-a041-fe6602b5bd4c" />

### Steps involved

<img width="400" height="375" alt="image" src="https://github.com/user-attachments/assets/2fb5b591-c94b-45be-81af-ffae09b49ccb" />

                           

   
     
     
