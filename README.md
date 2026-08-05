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
  

                                 [ Camera Stream ]
                                        │
                                        ▼
                      +----------------------------------+
                      |   TIER 1: CLIP (Global Vision)   |
                      |   - Understands scene context    |
                      |   - Detects accident / collision |
                      +-----------------+----------------+
                                        │
                         [ Accident Flagged: YES ]
                                        │
                                        ▼
                      +----------------------------------+
                      |   TIER 2: ALPR (Targeted Vision) |
                      |   - Isolates vehicle plate       |
                      |   - Extracts license plate OCR   |
                      +-----------------+----------------+
                                        │
                                        ▼
                           [ Emergency Alert & Log ]
                           

   
     
     
