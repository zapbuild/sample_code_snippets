# React-Native-Code-Samples

## App Description

These snippets are taken from [Insane Deals](https://play.google.com/store/apps/details?id=com.insanedeals) app codebase. The app provides the user with latest deals acorss the platforms like Amazon, Flipkart etc. based on the set preferences by the users.

The shared code files are related to the functionality of presenting the trending Categories, Brands to the user and allowing the user setup his/her preferences.
The tech-stack used in the app include React Navigation, Redux, Redux Thunk, Jest, Fetch Mock, Linking etc.

## Sample Files

### UserPreferenceActions.ts

A Redux Actions file that contains actions for fetching Categories, Brands and saving user preferences to the store and server. The libraries used includes Redux, Redux Thunk Middleware etc.

### UserPreferenceActions.test.ts

A TestCase file for UserPreference Actions. The libraries used includes Jest, Redux, Redux Thunk, Redux Mock Store, Fetch Mock etc.

### Logger.ts

A simple Logger function that only prints the Logs on Debug Enviornment.

### FetchUtils.ts

A Utils file that include boilerplate code for POST and GET requests used in the React Native apps. The libraries used includes Fetch, NetInfo, Logger etc.

### HandleResponse.ts

A custom Redux middleware that is used to print Log statements for requests and also fire reset actions in case of AUTH_ERROR.

## Thankyou

