<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AuthController;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| contains the "web" middleware group. Now create something great!
|
*/
#Redirect to dashboard
Route::get('/', [AuthController::class, 'dashboard']); 
#Show login form
Route::get('login', [AuthController::class, 'index'])->name('login');
#Post login details
Route::post('submit-login', [AuthController::class, 'postLogin'])->name('login.post'); 
#Show registration form
Route::get('registration', [AuthController::class, 'registration'])->name('register');
#Post registration Details
Route::post('submit-registration', [AuthController::class, 'postRegistration'])->name('register.post');
#User logout 
Route::get('logout', [AuthController::class, 'logout'])->name('logout');
