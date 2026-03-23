from django.shortcuts import render


def estimator(request):
    return render(request, 'widgets/estimator.html')


def focus_write(request):
    return render(request, 'widgets/focus_write.html')


def word_counter(request):
    return render(request, 'widgets/word_counter.html')


def advice(request):
    links = [
        {
            'title': "Jacob's College Application FAQ",
            'url': 'https://beautifulthorns.wixsite.com/home/post/jacob-s-college-application-faq-wip-week',
            'source': 'beautifulthorns.wixsite.com',
        },
        {
            'title': "Applying Sideways",
            'url': 'https://mitadmissions.org/blogs/entry/applying_sideways/',
            'source': 'mitadmissions.org',
        },
        {
            'title': "Writing, Briefly",
            'url': 'https://paulgraham.com/writing44.html',
            'source': 'paulgraham.com',
        },
        {
            'title': "Mikail's Thoughts about College Admissions",
            'url': 'https://docs.google.com/document/d/1U0fGlaeLvX-i2ZPhQti0JaPRP2YcqW8DsZ2DPvz6PvM/edit?tab=t.0',
            'source': 'docs.google.com',
        },
        {
            'title': "College advice for people who are exactly like me",
            'url': 'https://www.benkuhn.net/college/',
            'source': 'benkuhn.net',
        },
    ]
    return render(request, 'widgets/advice.html', {'links': links})
