# Quantum Bake
This add-on adds a Node to the shader editor, which functions as a Data-Container for a Streamlined Baking Process.

## Panel in Render Settings
![grafik](https://github.com/user-attachments/assets/be78f711-2fab-4232-9f2e-ba846aeb78f9)

All Materials on the selected mesh will be handled
No need to select a Dummy Image first.

The Add-on will search for the Nodes in every Material and handle the baking Process using blenders default node system.
Nodes Will be created in the background to handle the bake.
Images will be combined using "numpy" if necessary.

## Node

![grafik](https://github.com/user-attachments/assets/bf77402d-6933-4bcf-8fb6-7627fb34d27f)

### Image Name
The Image Name will be added as a suffix if no image reference image is selected. The automatic name will be put together using the Object name, material name, and Material name and the Image name. Best use with https://github.com/SaphiBlue/QExport 

### Bake Modes
  * Color, Color and Alpha
  * Packed, Uses a Red, Green, Red, Alpha input to generate a Packed Map
  * Normal, Uses a Shader input to bake normal maps
