# My Approach Documentation

## General Approach

Generally, my approach is as follows:
1. Thoroughly document requirements and needs.
2. Get general specifications set, including software architecting decisions.
3. Set-up infrastructure as needed.
4. Get an initial LLM shot done in order to get the most of the critical features done quickly.
5. Test and iterate locally to fix bugs, implement missed features, correct LLM mistakes, etc.
6. Deploy steadily as local testing indicates features are ready.

For git, my strategy usually involves:
1. Set things up via the main branch to rapidly get infrastructure and needed boiler plate in place.
2. Branch off using a `task_category/initials_specific-task` format for the branch name.
3. Use LLMs to identify and build context via planning modes/prompts, then implement.
4. Test results locally and iterate.
5. Push to new branch
6. Create a PR via github CLI
7. Iterate to pass linting and testing (or whatever CI steps I have implemented)
8. Squash and merge into main

I almost always do git commands myself.

## Tools Chosen

The general coding tools I chose for deployment are Firebase for deployment with the Google Vision API.
I chose Typescript for the frontend, and Python 3.11 for the backend functions.
The main reason for choosing these are because of the versatility and robustness of Firebase (and ease of connecting to Google Vision API), Python as a quick script for the funcitons that I am more familiar with (3.11 was somewhat arbitrary, but I wanted a stable Python 3 version), and Typescript as the leading language for frontend development.

For AI coding tools I used Claude Code and Gemini. The reasoning behind this is that they are a good pair of workhorse that follows instructions and creative critique for identifying issues and resolving them. They also both have CLIs that make it easy to work with them in Cursor.

## Known Limitations

There are a few specific limitations that need to be identified.
+ The OCR is not perfect. There are extensive checks to try and make sure that things are consistent and the critical componenets are there, but due to the nature of trying to be flexible with detection and get results, not everything can be precise.
+ The government warning checks for key words, including the capitalization of Surgeon General.
+ Due to fuzzy matching, names can be slightly misspelled and still pass.
+ I implemented more checks for various products (like wines needing a statement if they contain a certain level of sulfites). While I did these according to the CFR resources I found (and referenced) I am not an expert at these regulations, and cannot guarantee that they accurately reflect the requirements. They do seem consistent with my quick inspection, so for this MVP, I am calling them good.
+ Bounding boxes don't always appear when they are supposed to appear, and only capture the first part of the found text. This was in part because the point of the visual bounding box is so that a human can quickly identify the pieces, so as long as their eyes were drawn to the beginning, any manual checking can be done quickly.

## Maintainability

This repository is easily maintained as the main branch is automatically deployed to Firebase. Work should be done on a separate branch, pushed, and then merged into the `main` branch in order to deploy the frontend.
Functions should be deployed using `firebase deploy --only functions`.

## Assumptions

+ I assumed that this tool was not going to be used as an official government tool, and as such has a disclaimer.
+ I assumed that the priority was identifying issues with the labels, so I took the approach of trying to verify that critical components were present.

