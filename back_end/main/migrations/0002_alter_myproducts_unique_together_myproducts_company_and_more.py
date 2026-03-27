# Fixed migration file for main.0002
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        # Step 1: Add the `company` field to `MyProducts`.
        migrations.AddField(
            model_name='myproducts',
            name='company',
            field=models.ForeignKey(default='Company', on_delete=django.db.models.deletion.CASCADE, to='main.company'),
            preserve_default=False,
        ),
        # Step 2: Apply the new `unique_together` constraint.
        migrations.AlterUniqueTogether(
            name='myproducts',
            unique_together={('company', 'product')},
        ),
        # Step 3: Remove the `user` field.
        migrations.RemoveField(
            model_name='myproducts',
            name='user',
        ),
    ]
