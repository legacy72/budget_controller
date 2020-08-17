from django.contrib import admin

from .models import *


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'type', 'sum', 'created_date', )
    list_filter = ('user', )


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', )
    list_filter = ('name', )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'operation_type', 'code_name', )
    list_filter = ('name', 'operation_type', 'code_name', )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_operation_type', 'category', 'bill', 'sum', 'date', 'tag', 'comment', )
    list_filter = ('user', 'category__operation_type', 'category', 'bill', 'date', 'tag', )

    def get_operation_type(self, obj):
        return obj.category.operation_type.get_name_display()

    get_operation_type.short_description = 'Вид операции'


@admin.register(PlannedBudget)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'sum', 'date', )
    list_filter = ('user', 'category__operation_type', 'category', 'date', )

    def get_operation_type(self, obj):
        return obj.category.operation_type.get_name_display()

    get_operation_type.short_description = 'Планируемый бюджет'


@admin.register(AuthCode)
class AuthCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'start_date', 'end_date', )
    list_filter = ('user', 'code', 'start_date', 'end_date', )
