# Doge - Fusion 360 Dogbone Generator Plugin

Doge is a Fusion 360 plugin designed to automate the generation of dogbone features in your CAD models. It has the 
ability to update created dogebones, when the design or parameters changes. 

## Motivation?

Fusion 360 has an experimental custom feature API, which would be right tool to do the job. It's broken since it's 
announcements and is not moving in any direction. As I'm bored of re-creating features, every time I update the model
or change the tool diameter, I created this add-in to explore alternative ways of achieving dogbones that update when
the design changes.

## Usage

### Create Dogbones

1. Press `s` on the keyboard an type `dogebone`. Select `Create Dogebone`. Alternatively use the button in the modify panel
2. Select relevant faces and enter the tool radius. Expressions are supported as well, so you can dynamically change the radius of the tool.
3. Click okay

### Update dogbones

Whenever the design changes or parameter changes, Fusion won't update the Dogebones by itself. 

1. Press `s` on the keyboard and type `dogebone`. Select `Update Dogebone` and see your design updated.
2. Be lucky

## Installation

To use Doge in Fusion 360, follow these steps:

###

1. Install [Github to Fusion 360](https://apps.autodesk.com/FUSION/en/Detail/Index?id=789800822168335025&appLang=en&os=Mac) script
2. Run the script
3. Enter https://github.com/it-ony/doge as location

### Old fashioned way

1. [Download the latest release](https://github.com/it-ony/doge/archive/refs/heads/master.zip).
2. Unzip to a location, that you'll not delete
3. Open the add-ins and script panel
4. Go to add-ins
5. Click the plus sign 
6. Select the directory where the content is unzipped

## Credits

- The structure of this code was adapted from Florian Pommerening's [Fingerjoint Plugin](https://github.com/FlorianPommerening/FingerJoints).
- The dogbone algorithm is based on Peter Ludikar's [Dogebone Plugin](https://github.com/DVE2000/Dogbone), with contributions from various authors.
  See the [list of contributors](https://github.com/DVE2000/Dogbone#authors).

## License

This project is governed by the [MIT License](LICENSE). For a comprehensive understanding of the terms and conditions, 
please refer to the [LICENSE](LICENSE) file.

You are welcome to utilize, adapt, and distribute this code in your projects while adhering to the MIT License provisions.
