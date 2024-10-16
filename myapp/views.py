from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import *
from .models import *
from django.db.models import Q

from django.http import JsonResponse
from django.conf import settings
import os

import joblib
import numpy as np

def base(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'about/about.html')

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            #create a new registration object and avoid saving it yet
            new_user = user_form.save(commit=False)
            #reset the choosen password
            new_user.set_password(user_form.cleaned_data['password'])
            #save the new registration
            new_user.save()
            return render(request, 'registration/register_done.html',{'new_user':new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration/register.html',{'user_form':user_form})



def profile(request):
    return render(request, 'profile/profile.html')



@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = EditProfileForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        user_form = EditProfileForm(instance=request.user)
    
    return render(request, 'profile/edit_profile.html', {'user_form': user_form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, 'Your account was successfully deleted.')
        return redirect('base')  # Redirect to the homepage or another page after deletion

    return render(request, 'registration/delete_account.html')
# das


# Contact start
@login_required
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for contacting us!")
            return redirect('dashboard')  # Redirect to the same page to show the modal
    else:
        form = ContactForm()

    return render(request, 'contact/contact_form.html', {'form': form})

# contact end

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os

# Load the pre-trained models
spiral_model = load_model('model/parkinsons_spiral_model.h5')
wave_model = load_model('model/parkinsons_wave_model.h5')


def predict_parkinsons(model, img_path):
    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0  # Rescale pixel values

    prediction = model.predict(img_array)
    return "Parkinson's detected" if prediction[0] > 0.5 else "Healthy"

def get_suggestions_and_exercises(result):
    if result == "Parkinson's detected":
        suggestions = [
            "Consider consulting a neurologist for further assessment.",
            "Maintain a balanced diet rich in antioxidants.",
            "Engage in regular exercise, focusing on motor skills and flexibility.",
            "Practice activities like walking, swimming, or cycling to improve balance."
        ]
        exercises = [
            "1. Finger Tapping: Tap your thumb and each finger together rapidly for 30 seconds.",
            "2. Big Arm Movements: Practice wide arm swings to improve range of motion.",
            "3. Leg Lifts: Lift each leg while standing or sitting to strengthen muscles.",
            "4. Balance Exercises: Practice standing on one leg for 10 seconds."
        ]
    else:
        suggestions = [
            "Maintain a healthy lifestyle to prevent neurodegenerative diseases.",
            "Engage in regular physical activity, focusing on cardiovascular fitness.",
            "Practice mindfulness and cognitive exercises to keep your brain sharp."
        ]
        exercises = [
            "1. Walking: A 30-minute daily walk helps improve cardiovascular health.",
            "2. Brain Games: Solve puzzles or play memory games to enhance cognitive function.",
            "3. Stretching: Incorporate daily stretching to improve flexibility."
        ]
    return suggestions, exercises

def upload_image(request):
    if request.method == 'POST' and request.FILES['image']:
        image_file = request.FILES['image']
        fs = FileSystemStorage()
        file_path = fs.save(image_file.name, image_file)
        full_path = fs.path(file_path)

        selected_model = request.POST.get('model_choice')
        model = spiral_model if selected_model == 'spiral' else wave_model

        result = predict_parkinsons(model, full_path)

        # Get suggestions and exercises based on the result
        suggestions, exercises = get_suggestions_and_exercises(result)

        return render(request, 'parkinson/result.html', {
            'result': result,
            'suggestions': suggestions,
            'exercises': exercises
        })

    return render(request, 'parkinson/upload.html')


from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import json
from django.conf import settings

# Load the most accurate pre-trained model
best_model = load_model(os.path.join(settings.MEDIA_ROOT, 'model', 'best_parkinsons_model.h5'))

# Load model metrics from JSON file
metrics_file_path = os.path.join(settings.MEDIA_ROOT, 'model', 'model_metrics.json')
with open(metrics_file_path, 'r') as f:
    model_metrics = json.load(f)


def predict_parkinsons(model, img_path):
    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0  # Rescale pixel values

    prediction = model.predict(img_array)[0][0]
    
    # Determine if Parkinson's is detected based on the prediction threshold
    result = "Parkinson's detected" if prediction > 0.5 else "Healthy"
    
    # Calculate the percentage of how much the user is likely suffering
    prediction_percentage = round(prediction * 100, 2)
    
    # Determine the stage based on prediction percentage
    if prediction_percentage >= 80:
        stage = "Advanced"
    elif 50 <= prediction_percentage < 80:
        stage = "Moderate"
    elif 20 <= prediction_percentage < 50:
        stage = "Early Stage"
    else:
        stage = "No Symptoms"

    return result, prediction_percentage, stage



def get_suggestions_and_exercises(result):
    """Get health suggestions and exercises based on the prediction."""
    if result == "Parkinson's detected":
        suggestions = [
            "Consider consulting a neurologist for further assessment.",
            "Maintain a balanced diet rich in antioxidants.",
            "Engage in regular exercise, focusing on motor skills and flexibility.",
            "Practice activities like walking, swimming, or cycling to improve balance."
        ]
        exercises = [
            "1. Finger Tapping: Tap your thumb and each finger together rapidly for 30 seconds.",
            "2. Big Arm Movements: Practice wide arm swings to improve range of motion.",
            "3. Leg Lifts: Lift each leg while standing or sitting to strengthen muscles.",
            "4. Balance Exercises: Practice standing on one leg for 10 seconds."
        ]
    else:
        suggestions = [
            "Maintain a healthy lifestyle to prevent neurodegenerative diseases.",
            "Engage in regular physical activity, focusing on cardiovascular fitness.",
            "Practice mindfulness and cognitive exercises to keep your brain sharp."
        ]
        exercises = [
            "1. Walking: A 30-minute daily walk helps improve cardiovascular health.",
            "2. Brain Games: Solve puzzles or play memory games to enhance cognitive function.",
            "3. Stretching: Incorporate daily stretching to improve flexibility."
        ]
    return suggestions, exercises


def upload_image(request):
    """Handle the image upload and model prediction."""
    if request.method == 'POST' and request.FILES['image']:
        # Save uploaded image
        image_file = request.FILES['image']
        fs = FileSystemStorage()
        file_path = fs.save(image_file.name, image_file)
        full_path = fs.path(file_path)

        # Use the best model for prediction
        result = predict_parkinsons(best_model, full_path)

        # Get suggestions and exercises based on the result
        suggestions, exercises = get_suggestions_and_exercises(result)

        # Pass result, suggestions, exercises, and model metrics to the template
        return render(request, 'parkinson/result.html', {
            'result': result,
            'suggestions': suggestions,
            'exercises': exercises,
            'metrics': model_metrics  # Pass the model metrics for display
        })

    return render(request, 'parkinson/upload.html')
