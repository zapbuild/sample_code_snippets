# Architecture

I have submitted following files. All files are developed in Kotlin. These files have used MVVM and Singleton design patterns with koin, coroutine and data binding.

- BaseActivity
- BaseView
- BaseViewModel
- FacebookListener
- FacebookManager
- GoogleAuthListener
- GoogleAuthManager
- NetworkModule
- SecurityIntercepter


# Files Details

These files are developed in kotlin with support of minimum api version 16 to latest version.
We have used MVVM and Singleton design patterns with koin,coroutine and data binding.



## BaseActivity
    
This is base activity acts as base for all other activities. It contains common methods and functionalities.

## BaseView

This is an interface, contains all the methods for base activity.

## BaseViewModel

This class includes API requests/responses and exception handling for API calls.

## FacebookListener

This is an interface, contains methods for facebook callbacks.

## FacebookManager

This class contains calls/methods for facebook integration. Included success and failure handling.

## GoogleAuthListener

This is an interface, contains methods for google callbacks.

## GoogleAuthManager

This class contains calls/methods for Google integration. Included success and failure handling.

## NetworkModule

This class contains all the network realted functions, add okhttp, build APIService, add custom and logging intercepter.


## SecurityIntercepter

This class is used to add headers to API's request and build chains.


