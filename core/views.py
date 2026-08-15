import json
from functools import lru_cache
from urllib import request

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .models import LibraryBook, Subscription


GUEST_EMAIL = 'guest@gmail.com'
GUEST_PASSWORD = 'guest123'

BOOK_API_URL = 'https://us-central1-summaristt.cloudfunctions.net'


def _api_get(url):
    req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode('utf-8'))


def _normalize_book(raw):
    if not isinstance(raw, dict):
        return {}
    book = {
        'id': raw.get('id', ''),
        'author': raw.get('author', ''),
        'title': raw.get('title', ''),
        'subtitle': raw.get('subTitle') or raw.get('subtitle') or '',
        'image': raw.get('imageLink') or raw.get('image') or '',
        'audio_url': raw.get('audioLink') or raw.get('audio_url') or '',
        'total_rating': raw.get('totalRating', raw.get('total_rating', 0)),
        'average_rating': raw.get('averageRating', raw.get('average_rating', 0)),
        'key_ideas': raw.get('keyIdeas', raw.get('key_ideas', 0)),
        'type': raw.get('type', ''),
        'status': raw.get('status', ''),
        'subscription_required': bool(raw.get('subscriptionRequired', raw.get('subscription_required', False))),
        'summary': raw.get('summary', ''),
        'tags': raw.get('tags', []),
        'description': raw.get('bookDescription') or raw.get('description') or '',
        'author_description': raw.get('authorDescription') or raw.get('author_description') or '',
        'rating': float(raw.get('averageRating', raw.get('average_rating', 0)) or 0),
    }
    return book


@lru_cache(maxsize=32)
def _get_books_for_status(status):
    url = f'{BOOK_API_URL}/getBooks?status={status}'
    try:
        payload = _api_get(url)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [_normalize_book(item) for item in payload if isinstance(item, dict)]


@lru_cache(maxsize=256)
def _get_book_by_id(book_id):
    url = f'{BOOK_API_URL}/getBook?id={book_id}'
    try:
        payload = _api_get(url)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return _normalize_book(payload)


@lru_cache(maxsize=128)
def _search_books(query):
    search_term = (query or '').strip()
    if not search_term:
        return []
    url = f'{BOOK_API_URL}/getBooksByAuthorOrTitle?search={search_term}'
    try:
        payload = _api_get(url)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [_normalize_book(item) for item in payload if isinstance(item, dict)]


LEGACY_BOOK_ALIASES = {
    'atomic-habits': 'f9gy1gpai8',
    'deep-work': 'f9gy1gpai8',
    'the-lean-startup': 'f9gy1gpai8',
}

GUEST_FINISHED_BOOK_IDS = ['f9gy1gpai8', '5bxl50cz4bt']


def _ensure_guest_library_state(user):
    if not user or not user.is_authenticated or user.email != GUEST_EMAIL:
        return
    for book_id in GUEST_FINISHED_BOOK_IDS:
        book = _get_book_by_id(book_id)
        if not book:
            continue
        LibraryBook.objects.get_or_create(
            user=user,
            book_id=book_id,
            defaults={'title': book['title'], 'finished': True},
        )
        LibraryBook.objects.filter(user=user, book_id=book_id).update(finished=True)


def _resolve_book_id(book_id):
    if not book_id:
        return None
    if _get_book_by_id(book_id):
        return book_id
    resolved = LEGACY_BOOK_ALIASES.get(book_id)
    if resolved and _get_book_by_id(resolved):
        return resolved
    selected = _get_books_for_status('selected')
    return selected[0]['id'] if selected else None


def home(request):
    featured = _get_books_for_status('selected')
    return render(request, 'home.html', {'featured_books': featured})


def _user_subscription(user):
    if not user or not user.is_authenticated:
        return 'Basic'
    sub = Subscription.objects.filter(user=user, is_active=True).order_by('-created_at').first()
    return (sub.plan.title() if sub else 'Basic')


def for_you(request):
    selected = _get_books_for_status('selected')[:1]
    recommended = _get_books_for_status('recommended')[:3]
    suggested = _get_books_for_status('suggested')[:3]
    if request.user.is_authenticated:
        _ensure_guest_library_state(request.user)
    return render(
        request,
        'for_you.html',
        {
            'selected_book': selected[0] if selected else None,
            'recommended_books': recommended,
            'suggested_books': suggested,
        },
    )


def book_detail(request, book_id):
    resolved_id = _resolve_book_id(book_id)
    book = _get_book_by_id(resolved_id)
    if not book:
        selected = _get_books_for_status('selected')
        book = selected[0] if selected else None
    return render(request, 'book_detail.html', {'book': book})


def choose_plan(request):
    if request.method == 'POST':
        plan = request.POST.get('plan', 'basic')
        if request.user.is_authenticated:
            Subscription.objects.update_or_create(user=request.user, defaults={'plan': plan, 'is_active': True})
            return redirect('settings')
    return render(request, 'choose_plan.html')


def player(request, book_id):
    resolved_id = _resolve_book_id(book_id)
    book = _get_book_by_id(resolved_id)
    if not book:
        selected = _get_books_for_status('selected')
        book = selected[0] if selected else None
    return render(request, 'player.html', {'book': book})


def handle_auth(request):
    if request.method != 'POST':
        return redirect('home')

    email = (request.POST.get('email') or '').strip()
    password = request.POST.get('password') or ''
    action = request.POST.get('action') or 'login'

    if '@' not in email or '.' not in email.split('@')[-1]:
        return render(request, 'home.html', {'auth_error': 'Invalid email'})

    if action == 'register':
        if len(password) < 6:
            return render(request, 'home.html', {'auth_error': 'Short password'})
        username = email.split('@')[0]
        if not username:
            return render(request, 'home.html', {'auth_error': 'Invalid email'})
        user_exists = __import__('django.contrib.auth').contrib.auth.get_user_model().objects.filter(email=email).exists()
        if user_exists:
            return render(request, 'home.html', {'auth_error': 'User already exists'})
        user = __import__('django.contrib.auth').contrib.auth.get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        login(request, user)
        return redirect('for_you')

    if email == GUEST_EMAIL and password == GUEST_PASSWORD:
        user, _ = __import__('django.contrib.auth').contrib.auth.get_user_model().objects.get_or_create(
            username='guestuser',
            defaults={'email': email},
        )
        if not user.check_password(password):
            user.set_password(password)
            user.save()
        login(request, user)
        return redirect('for_you')

    user = authenticate(request, username=email.split('@')[0], password=password)
    if user is None:
        user = authenticate(request, email=email, password=password)
    if user is None:
        return render(request, 'home.html', {'auth_error': 'User not found'})

    login(request, user)
    return redirect('for_you')


def logout_user(request):
    logout(request)
    return redirect('home')


def settings(request):
    user_email = request.user.email if request.user.is_authenticated else 'guest@gmail.com'
    subscription = _user_subscription(request.user)
    return render(request, 'settings.html', {
        'user_email': user_email,
        'subscription': subscription,
    })


def library(request):
    if not request.user.is_authenticated:
        return render(request, 'library.html', {
            'library_books': [],
            'finished_books': [],
        })

    _ensure_guest_library_state(request.user)

    saved_books = LibraryBook.objects.filter(user=request.user, finished=False).order_by('-created_at')
    finished_books_qs = LibraryBook.objects.filter(user=request.user, finished=True).order_by('-created_at')

    library_books = []
    for item in saved_books:
        book = _get_book_by_id(item.book_id)
        if book:
            library_books.append(book)

    finished_books = []
    for item in finished_books_qs:
        book = _get_book_by_id(item.book_id)
        if book:
            finished_books.append(book)

    return render(request, 'library.html', {
        'library_books': library_books,
        'finished_books': finished_books,
    })


def save_book(request, book_id):
    if not request.user.is_authenticated:
        return redirect('home')
    resolved_id = _resolve_book_id(book_id)
    book = _get_book_by_id(resolved_id)
    if not book:
        return redirect('for_you')
    LibraryBook.objects.get_or_create(user=request.user, book_id=resolved_id, defaults={'title': book['title']})
    return redirect('library')


def search(request):
    query = (request.GET.get('q') or '').strip()
    results = _search_books(query)
    return render(request, 'search.html', {
        'query': query,
        'results': results,
    })
