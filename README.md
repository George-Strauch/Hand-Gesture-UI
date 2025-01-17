# Hand Gestures

A project that aims at performing specific actions using hand gestures. It leverages computer vision and hand detection techniques to recognize the gestures accurately.

## Introduction

This repository contains the source code for hand gesture recognition, state flow, and display. The project is built with the goal of creating an intuitive way of interfacing with technology. using a flask server to provide information to a front end interface
## Features

- **Active / Inactive**: Ability to determine if the user is in a state where they want their hand gesture to be detected.
- **Gesture Detection**: Detects hand gesture action within the context of what state the interface is in.
- **State Transforms**: Transforms between states such as awake / asleep or sub-menus
- **Actions**: Performs set of specific actions based on recognized gesture and state. In the current context, this is being used to control a smart tv, however it can easily be abstracted to other actions or uses. 


## Project Structure
![alternative text](media/model_layout.png)


