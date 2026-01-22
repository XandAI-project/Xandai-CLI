<?php

/**
 * Laravel Routes Example
 */

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\UserController;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\OrderController;

// User routes
Route::get('/api/users', [UserController::class, 'index']);
Route::post('/api/users', [UserController::class, 'store']);
Route::get('/api/users/{id}', [UserController::class, 'show']);
Route::put('/api/users/{id}', [UserController::class, 'update']);
Route::delete('/api/users/{id}', [UserController::class, 'destroy']);

// Product routes
Route::get('/api/products', [ProductController::class, 'index']);
Route::post('/api/products', [ProductController::class, 'store']);
Route::get('/api/products/{id}', [ProductController::class, 'show']);

// Order routes
Route::get('/api/orders', [OrderController::class, 'index']);
Route::post('/api/orders', [OrderController::class, 'store']);
Route::patch('/api/orders/{id}', [OrderController::class, 'update']);
Route::delete('/api/orders/{id}', [OrderController::class, 'destroy']);

// Authentication routes
Route::post('/api/auth/login', [AuthController::class, 'login']);
Route::post('/api/auth/register', [AuthController::class, 'register']);
Route::post('/api/auth/logout', [AuthController::class, 'logout']);
