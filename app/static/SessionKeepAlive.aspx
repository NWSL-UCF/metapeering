protected void Page_Load(object sender, EventArgs e){
    Response.AddHeader("Refresh", Convert.ToString((Session.Timeout * 60) - 10));
}