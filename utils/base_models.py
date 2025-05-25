from django.db import models

class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted =models.BooleanField(default=False)
    created_by = models.CharField(max_length=255, null=True, blank=True)  
    updated_by = models.CharField(max_length=255, null=True, blank=True)  
    
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # super().save(*args, **kwargs)
        if self.pk:
            old_instance= self.__class__.objects.get(pk=self.pk)
            if old_instance.is_deleted != self.is_deleted:
                print("In is_deleted")
                # Trigger cascading updates across related models
                self.update_related_models()
        super().save(*args, **kwargs)

    def update_related_models(self):
        # Recursively update all related models
        print("1")
        self._update_related_models_recursively(self)

    def _update_related_models_recursively(self, instance):
        related_objects = instance._meta.related_objects

        for related_object in related_objects:
            related_model = related_object.related_model
            related_field_name = related_object.field.name

            # Skip many-to-many relationships
            if related_object.many_to_many:
                print(f"Skipping many-to-many relationship: {related_object.related_model.__name__}")
                continue

            # Skip non-CASCADE relationships
            if related_object.on_delete != models.CASCADE:
                print(f"Skipping non-CASCADE relationship: {related_object.related_model.__name__} with on_delete={related_object.on_delete}")
                continue

            if hasattr(related_model, 'is_deleted'):
                print(f"Updating model: {related_model.__name__} for {related_field_name}={instance}")
                # Update all related instances
                related_instances = related_model.objects.filter(**{related_field_name: instance})
                related_instances.update(is_deleted=instance.is_deleted)

                # For each related instance, recursively update its related models
                for related_instance in related_instances:
                    self._update_related_models_recursively(related_instance)
            else:
                print(f"Skipping model: {related_model.__name__} for {related_field_name}={instance}")
    
