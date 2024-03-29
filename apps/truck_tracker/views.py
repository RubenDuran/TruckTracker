from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Count
from . models import User, Truck, Category, Color
import bcrypt
import urllib
from . import twilio_config as twilio


def index(request):
    last_truck = Truck.objects.latest('created_at')
    total_trucks = Truck.objects.count()
    print last_truck.category.category_name
    print total_trucks
    context = {
        'last_truck': last_truck,
        'total_trucks': total_trucks
    }
    return render(request, 'truck_tracker/index.html', context)


def trucks(request):
    last_truck = Truck.objects.latest('created_at')
    total_trucks = Truck.objects.count()
    # truck_categories = Category.objects.all()
    truck_categories = Category.objects.annotate(
        number_of_trucks=Count('truck')).order_by('category_name')
    print truck_categories[0].number_of_trucks
    context = {
        'truck_categories': truck_categories,
        'last_truck': last_truck,
        'total_trucks': total_trucks
    }
    return render(request, 'truck_tracker/trucks.html', context)


# Author.objects.filter(name__unaccent__icontains='Helen')
def search(request):
    print "the request:"
    print request
    print "the request.GET:"
    print request.GET
    truck_categories = Category.objects.filter(category_name__icontains=request.GET[
                                               "search"]).annotate(number_of_trucks=Count('truck')).order_by('category_name')
    print truck_categories
    context = {
        'truck_categories': truck_categories,
    }
    return render(request, 'truck_tracker/search.html', context)


def add_truck(request):
    last_truck = Truck.objects.latest('created_at')
    total_trucks = Truck.objects.count()
    truck_categories = Category.objects.all().order_by('category_name')
    context = {
        'truck_categories': truck_categories,
        'last_truck': last_truck,
        'total_trucks': total_trucks
    }
    return render(request, 'truck_tracker/add.html', context)


def add(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/')
    if request.method == 'POST' and request.FILES['img']:
        category = request.POST['category']
        category = Category.objects.get(category_name=category)
        p_color = request.POST['primary_color']
        s_color = request.POST['secondary_color']
        img = request.FILES['img']
        print img
        user = User.objects.get(pk=request.session['user_id'])
        users = User.objects.all()

        truck = Truck.objects.create(
            user=user, category=category, document=img)
        color = Color.objects.create(primary_color=p_color,
                                     secondary_color=s_color, truck_color=truck)

        for _ in users:
            twilio.client.messages.create(
                to=_.phone,
                from_="+14803728939",
                body="New {} Truck Added by: {}.".format(
                    category.category_name, user.username),
                media_url=["http://jacobduran.com/media/documents/{}".format(img)])

        # errors = Truck.objects.validate(request.POST)
        # if errors:
        #     for error in errors:
        #         messages.error(request, error)
        # else:
        #     print request.POST['category']

    return redirect('/category/{}'.format(category.category_name))


def delete(request):
    return redirect('/trucks')


def logout(request):
    del request.session['user_id']
    return redirect('/')


def register(request):
    if request.method == 'POST':
        errors = User.objects.validate(request.POST)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            messages.success(request, 'Successfully registered!')
            hashed = bcrypt.hashpw(
                request.POST['pw'].encode(), bcrypt.gensalt())

            user_phone = "+1" + str(request.POST['phone_one']) + str(
                request.POST['phone_two']) + str(request.POST['phone_three'])
            print user_phone

            User.objects.create(f_name=request.POST['f_name'], l_name=request.POST['l_name'], username=request.POST[
                                'username'], password=hashed, created_at='NOW()', updated_at='NOW()', phone=user_phone)
            username = request.POST["username"]
            user_details = User.objects.filter(username=username)
            user = user_details[0]
            request.session['user_id'] = user.id

            twilio.client.messages.create(
                to=user_phone,
                from_="+14803728939",
                body="Thanks for signing up! You'll receive a notification" +
                "everytime a new truck gets added. - http://jacobduran.com")
            return redirect('/trucks')
    return redirect('/')


def login(request):
    if request.method == 'POST':
        errors = User.objects.signin(request.POST)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            messages.success(request, 'Successfully logged in!')
            username = request.POST["username"]
            user_details = User.objects.filter(username=username)
            user = user_details[0]
            request.session['user_id'] = user.id
            return redirect('/add_truck')
        return redirect('/')


def category(request, id):

    last_truck = Truck.objects.latest('created_at')
    total_trucks = Truck.objects.count()

    category = urllib.unquote(id).decode('utf8')
    print category
    trucks = Color.objects.filter(
        truck_color__category__category_name=category)
    context = {
        'category': category,
        'trucks': trucks,
        'last_truck': last_truck,
        'total_trucks': total_trucks
    }

    return render(request, 'truck_tracker/category.html', context)


def specific_truck(request, id, truck_id):
    return render(request, 'truck_tracker/truck.html')


def find(request):
    last_truck = Truck.objects.latest('created_at')
    total_trucks = Truck.objects.count()

    # category = urllib.unquote(id).decode('utf8')
    # print category
    truck = Color.objects.all().order_by('?')[0]
    context = {
        # 'category': category,
        'truck': truck,
        'last_truck': last_truck,
        'total_trucks': total_trucks
    }

    return render(request, 'truck_tracker/find.html', context)
