$(function () {
	$('[data-toggle="tooltip"]').tooltip()
});
 
function changeIssueStatusFunc(issue_current_status,issue_id){
	var checkBox = document.getElementById("checkbox_not_solved_issue_"+issue_id);
	var div_not_solved = document.getElementById("div_not_solved_"+issue_id);
	var div_solved = document.getElementById("div_solved_"+issue_id);
  	if (checkBox.checked == true){
	  	r = confirm("Confirm the issue is fixed?")
	  	if (r == true){
    		div_solved.style.display = "block";
    		div_not_solved.style.display = "none";
    	}
    	else{
    		checkBox.checked = false
    	}
    }
} 