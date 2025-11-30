from django.db import models

# Create your models here.

class Note(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    content = models.TextField("Содержимое", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Заметка"
        verbose_name_plural = "Заметки"

    def __str__(self) -> str:
        return self.title

