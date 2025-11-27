// Дополнительные функции JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое скрытие alert сообщений
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});