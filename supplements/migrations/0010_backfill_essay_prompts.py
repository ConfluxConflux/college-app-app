"""Give existing essays an EssayPrompt row so every essay has the same shape.

Essays imported before EssayPrompt keep their text in SupplementEssay.prompt.
Backfilling one prompt each (auto-selected) means a plain essay and a
"choose one of the following" essay are the same thing with a different count,
rather than two code paths.

SupplementEssay.prompt is left in place: prompt_text still reads it, so an
essay is never silently blanked if anything here is imperfect.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    SupplementEssay = apps.get_model('supplements', 'SupplementEssay')
    EssayPrompt = apps.get_model('supplements', 'EssayPrompt')

    made = 0
    for essay in SupplementEssay.objects.all():
        if essay.prompts.exists():
            continue
        text = (essay.prompt or '').strip()
        if not text:
            continue  # nothing to carry over; the essay can get a prompt later
        prompt = EssayPrompt.objects.create(
            essay=essay, text=text,
            word_limit=essay.word_limit, char_limit=essay.char_limit,
            sort_order=0,
        )
        essay.selected_prompt = prompt
        essay.save(update_fields=['selected_prompt'])
        made += 1
    print(f'  gave {made} existing essay(s) a prompt row')


def backwards(apps, schema_editor):
    """Copy the selected prompt's text back down, then drop the rows."""
    SupplementEssay = apps.get_model('supplements', 'SupplementEssay')
    EssayPrompt = apps.get_model('supplements', 'EssayPrompt')
    for essay in SupplementEssay.objects.filter(selected_prompt__isnull=False):
        essay.prompt = essay.selected_prompt.text
        essay.selected_prompt = None
        essay.save(update_fields=['prompt', 'selected_prompt'])
    EssayPrompt.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('supplements', '0009_essayprompt_supplementessay_selected_prompt'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
