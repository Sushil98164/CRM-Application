document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form.disable-on-submit');
    const cancelBtn = document.getElementById('cancelBtn')
    const editBtn = document.getElementById('editBtn')
    const viewBtn = document.getElementById('viewBtn')
    const clearFilterBtn = document.getElementById('clearFilterBtn')
    const punchOutCancelBtn = document.getElementById('punchOutCancelBtn')
    const addModalCancelBtn =  document.getElementById('addModalCancelBtn')
    const editModalcancelBtn = document.getElementById('editModalcancelBtn')

    forms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            const submitBtn = form.querySelector('button[type="submit"]');

            if (submitBtn && !submitBtn.disabled) {
                // Disable the button and show the loader
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loader"></span>';
            } else {
                // Prevent form submission if button is already disabled
                event.preventDefault();
                return false;
            }
        });
    });

    // Reset buttons when navigating back
    window.addEventListener('pageshow', function () {
        forms.forEach(function (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false; 
                submitBtn.innerHTML = 'Submit';
            }
        });
    });
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', function() {
            clearFilterBtn.disabled = true;
            clearFilterBtn.innerHTML = '<span class="loader cancel-btn"></span>';
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            cancelBtn.disabled = true;
            cancelBtn.innerHTML = '<span class="loader cancel-btn"></span>';
            setTimeout(() => {
                cancelBtn.disabled = false;
                cancelBtn.innerHTML = 'Cancel';
            }, 500);
        });
    }

    if (editBtn) {
        editBtn.addEventListener('click', function() {
            editBtn.disabled = true;
            editBtn.innerHTML = '<span class="loader edit-btn"></span>';
            setTimeout(() => {
                editBtn.disabled = false;
                editBtn.innerHTML = 'Edit';
            }, 300);
        });
    }

    if (viewBtn) {
        viewBtn.addEventListener('click', function() {
            viewBtn.disabled = true;
            viewBtn.innerHTML = '<span class="loader edit-btn"></span>';
        });
    }

    if (punchOutCancelBtn) {
        punchOutCancelBtn.addEventListener('click', function() {
            punchOutCancelBtn.disabled = true;
            punchOutCancelBtn.innerHTML = '<span class="loader cancel-btn"></span>';
            setTimeout(() => {
                punchOutCancelBtn.disabled = false;
                punchOutCancelBtn.innerHTML = 'Cancel';
            }, 300);
        });
    }

    if(addModalCancelBtn){
        addModalCancelBtn.addEventListener('click',function(){

        addModalCancelBtn.disabled = true;
        addModalCancelBtn.innerHTML = '<span class="loader cancel-btn"></span>';
        setTimeout(function() {
            addModalCancelBtn.disabled = false;
            addModalCancelBtn.innerHTML = 'Cancel'; 
            $('#myModal').modal('hide');
        }, 500);
    });
    }

    if (editModalcancelBtn){
        editModalcancelBtn.addEventListener('click',function(){
            var modalId = this.getAttribute('modalId');
            this.disabled = true;
            this.innerHTML = '<span class="loader cancel-btn"></span>';

            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = 'Cancel';
                $('#' + modalId).modal('hide');
            }, 500);

        });
    }
});
