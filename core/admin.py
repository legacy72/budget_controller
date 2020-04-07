from django.contrib import admin

from .models import *


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'sum', 'created_date', )
    list_filter = ('user', )


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', )
    list_filter = ('name', )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'operation_type', )
    list_filter = ('name', 'operation_type', )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_operation_type', 'category', 'bill', 'sum', 'date', 'tag', 'comment', )
    list_filter = ('user', 'category__operation_type', 'category', 'bill', 'date', 'tag', )

    def get_operation_type(self, obj):
        return obj.category.operation_type.get_name_display()

    get_operation_type.short_description = 'Вид операции'
