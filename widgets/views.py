from django.shortcuts import render


def estimator(request):
    return render(request, 'widgets/estimator.html')


def focus_write(request):
    return render(request, 'widgets/focus_write.html')


def word_counter(request):
    return render(request, 'widgets/word_counter.html')


def resources(request):
    links = [
        {
            'title': "CollegeVine (good for building a list & estimating your chances, but take with salt)",
            'url': 'http://collegevine.com/',
            'source': 'collegevine.com',
        },
        {
            'title': "MIT Admissions Blog",
            'url': 'https://mitadmissions.org/blogs/',
            'source': 'mitadmissions.org',
        },
        {
            'title': "The Notorious A2C (but don't get sucked down the distraction hole)",
            'url': 'https://www.applyingto.college/home',
            'source': 'applyingto.college',
        },
        {
            'title': "Admissions Matters (supposedly comprehensive book that I've never read)",
            'url': 'https://www.amazon.com/Admission-Matters-Students-Parents-Getting/dp/1119885736/',
            'source': 'amazon.com',
        },
        {
            'title': "3Blue1Brown Soundtrack (my favorite music for focusing)",
            'url': 'https://vincerubinetti.bandcamp.com/album/the-music-of-3blue1brown',
            'source': 'vincerubinetti.bandcamp.com',
        },
    ]
    return render(request, 'widgets/resources.html', {'links': links})


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
            'title': "College advice for people who are exactly like me",
            'url': 'https://www.benkuhn.net/college/',
            'source': 'benkuhn.net',
        },
        {
            'title': "Thoughts about College Admissions",
            'url': 'https://docs.google.com/document/d/1FPAK8zeqHCmVRaXMxDT-ylCUug04YqhS6Lf9ypynP5g/edit?tab=t.0',
            'source': 'docs.google.com',
        },
        {
            'title': "Writing, Briefly",
            'url': 'https://paulgraham.com/writing44.html',
            'source': 'paulgraham.com',
        },
    ]
    return render(request, 'widgets/advice.html', {'links': links})
