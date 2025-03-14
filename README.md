# Trisma: A Remote Screen Sharing and Control System

Trisma is a remote screen sharing and control system that allows users to share their screen with others and control their mouse and keyboard inputs. It is designed to be easy to use and provide a seamless experience for both the sharer and the viewer.

## Features

* **Screen Sharing**: Trisma allows users to share their screen with others in real-time. This means that the viewer can see exactly what the sharer is seeing on their screen.
* **Mouse and Keyboard Control**: Trisma allows the viewer to control the mouse and keyboard inputs of the sharer. This means that the viewer can interact with the sharer's screen.
* **Automatic Refresh**: Trisma will automatically refresh the screen every few seconds to ensure that the viewer is always seeing the most up-to-date information.
* **Configurable Resolution**: Trisma allows the user to configure the resolution of the shared screen. This means that the user can choose to share their screen at a lower resolution if they want to reduce the amount of bandwidth used.
* **Configurable Refresh Rate**: Trisma allows the user to configure the refresh rate of the shared screen. This means that the user can choose to refresh the screen at a slower rate if they want to reduce the amount of bandwidth used.

## Technical Details

Trisma is built using the following technologies:

* **Python**: Trisma is built using Python 3.6 or later.
* **Flask**: Trisma uses Flask as its web framework.
* **WebSockets**: Trisma uses WebSockets to establish a real-time communication channel between the sharer and the viewer.
* **PyAutoGUI**: Trisma uses PyAutoGUI to control the mouse and keyboard inputs of the sharer.
* **MSS**: Trisma uses MSS to capture the screen of the sharer.
* **Pillow**: Trisma uses Pillow to process the captured screen.

## Setup

To set up Trisma, follow these steps:

1. Install the required packages by running `pip install -r requirements.txt`.
2. Run the server by running `python server.py`.
3. Open a web browser and navigate to `http://localhost:8080`.
4. Click on the "Share Screen" button to share your screen.
5. The viewer can then navigate to `http://localhost:8080` and click on the "View Screen" button to view the shared screen.

## Limitations

Trisma allows the client to connect to the server from anywhere in the world, as long as the client can reach the server. Ensure that the server is accessible over the network for remote connections.

## Future Plans

We are currently working on adding the following features to Trisma:

* **Remote Screen Sharing**: We are working on adding support for sharing the screen of a remote machine.
* **Multi-User Support**: We are working on adding support for multiple users to share their screens at the same time.
* **Authentication**: We are working on adding support for authentication to ensure that only authorized users can share their screens.
* **Audio/Mic Sharing**: We are working on adding support for sharing audio and microphone input.

## Contributing

If you would like to contribute to Trisma, please follow these steps:

1. Fork the repository on GitHub.
2. Make your changes and commit them to your fork.
3. Create a pull request to merge your changes into the main repository.

We welcome any contributions, whether it be bug fixes, new features, or improvements to the documentation.
