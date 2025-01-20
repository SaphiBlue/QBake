# Quantum Bake
This add-on adds a Node to the shader editor, which functions as a Data-Container for a Streamlined Baking Process, and mass export.

## Panel in Render Settings
![export](https://github.com/user-attachments/assets/1c4f75d3-88c4-4471-8eb0-5a68fa7d4b32)


All Materials on the selected mesh will be handled
No need to select a Dummy Image first.

The Add-on will search for the Nodes in every Material and handle the baking Process using blenders default node system.
Nodes Will be created in the background to handle the bake.
Images will be combined using "numpy" if necessary.

## Node

![grafik](https://github.com/user-attachments/assets/89ef2d52-6bf3-47b1-b28b-1f11a38d3543)


### Image Name
The Image Name will be added as a suffix if no image reference image is selected. The automatic name will be put together using the Object name, material name, and Material name and the Image name. 

### Bake Modes
  * Color, Color and Alpha
  * Packed, Uses a Red, Green, Red, Alpha input to generate a Packed Map
  * Normal, Uses a Shader input to bake normal maps
