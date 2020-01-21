<?php

function listaLog () 
{
  //echo '<option selected value="">--- nenhuma ---</option>';
  $path = "log/";
  $diretorio = dir($path);
  while($arquivo = $diretorio -> read()){
    
    if ($arquivo == '.' || $arquivo == '..') {
      continue;
    }
    if ($arquivo == 'log.txt') {
      echo "<option selected value=".$arquivo.">".$arquivo."</option>";
    } else {
      echo "<option value=".$arquivo.">".$arquivo."</option>";
    }
  }
  $diretorio -> close();
}

?>
<!DOCTYPE html>
<html lang="en">
   <head>
      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
      <!-- Meta, title, CSS, favicons, etc. -->
      <meta charset="utf-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="icon" href="images/favicon.ico" type="image/ico" />

      <title>Lago Sul</title>

      <!-- Bootstrap -->
      <link href="../vendors/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">
      <!-- Font Awesome -->
      <link href="../vendors/font-awesome/css/font-awesome.min.css" rel="stylesheet">
      <!-- NProgress -->
      <link href="../vendors/nprogress/nprogress.css" rel="stylesheet">
      <!-- Custom Theme Style -->
      <link href="../build/css/custom.min.css" rel="stylesheet">
   </head>

<body class="nav-md">
    <div class="container body">
      <div class="main_container">
        <div class="col-md-3 left_col">
          <div class="left_col scroll-view">
            <div class="navbar nav_title" style="border: 0;">
              <a href="index.html" class="site_title"><i class="fa fa-globe"></i> <span>CEINTEL</span></a>
            </div>

            <div class="clearfix"></div>

            <!-- menu profile quick info -->
            <div class="profile clearfix">
              <div class="profile_pic">
                <img src="images/lagosul.jpg" alt="..." class="img-circle profile_img">
              </div>
              <div class="profile_info">
                <span>Bem vindo,</span>
                <h2>Lago Sul</h2>
              </div>
            </div>
        
           <div id="sidebar-menu" class="main_menu_side hidden-print main_menu">
              <div class="menu_section">
                
				
				<ul class="nav side-menu">
				
		    <li><a><i class="fa fa-desktop"></i> Monitor <span class="fa fa-chevron-down"></span></a>
                    <ul class="nav child_menu">				                        
                      
		      <li><a href="log.php">Log CMM</a></li>
		      				  
		     </ul>
                  </li> 
                   
                </ul>
              </div>
            </div>

            <!-- /sidebar menu -->
            <!-- /menu footer buttons -->
            <div class="sidebar-footer hidden-small">
               <a data-toggle="tooltip" data-placement="top" title="Settings">
               <span class="glyphicon glyphicon-cog" aria-hidden="true"></span>
               </a>
               <a data-toggle="tooltip" data-placement="top" title="FullScreen">
               <span class="glyphicon glyphicon-fullscreen" aria-hidden="true"></span>
               </a>
               <a data-toggle="tooltip" data-placement="top" title="Lock">
               <span class="glyphicon glyphicon-eye-close" aria-hidden="true"></span>
               </a>
               <a data-toggle="tooltip" data-placement="top" title="Logout" href="login.html">
               <span class="glyphicon glyphicon-off" aria-hidden="true"></span>
               </a>
            </div>


            <!-- /menu footer buttons -->
         </div>
      </div>
      <!-- page content -->
      <div class="right_col" role="main">
      <div class="">
      <div class="page-title">
         <div class="title_left">
            <h3>Monitor I/O</h3>
         </div>
      </div>
      <div class="clearfix"></div>
      <div class="row">
      <div class="col-md-16 col-sm-16 col-xs-16">
         <div class="x_panel">
            <div class="x_title">
               <h2>Log do Sistema</h2>
               <ul class="nav navbar-right panel_toolbox">                    
               </ul>
               <div class="clearfix"></div>
            </div>
            <div id="mensagem_alert">
            </div>
            <div class="form-group">
            <center><label class="control-label col-md-2"><h2>Mês</h2></a></label></center>
            <div class="col-sm-3">
            <select class="select2_group form-control" id="log" name="log"> 
              <option value="log.txt">log.txt</option>
              <option value="Janeiro">Janeiro</option>
              <option value="Fevereiro">Fevereiro</option>                            
              <option value="Março">Março</option>
              <option value="Abril">Abril</option>
              <option value="Maio">Maio</option>
              <option value="Junho">Junho</option>
              <option value="Julho">Julho</option>
              <option value="Agosto">Agosto</option>
              <option value="Setembro">Setembro</option>
              <option value="Outubro">Outubro</option> 
              <option value="Novembro">Novembro</option>
              <option value="Dezembro">Dezembro</option>
              
            </select>
            </div>
            </div>
            <div class="form-group">
            <center><label class="control-label col-md-2"><h2>Dia</h2></a></label></center>
            <div class="col-sm-3">
            <select class="select2_group form-control" id="arquivos" name="arquivos"> 
                                        
            </select>
            </div>
            </div>
            <textarea name="conteudo_log" id="conteudo_log" style="width:100%" rows="20"></textarea>
            <br><br>

	    <form action="comandos.php" method="post"> 
           	 <center><input id="botao" name="botao" type="submit" title="Este Botão reinicia o equipamento, leva cerca de 15 segundos..." class="btn btn-danger" value="Reiniciar o Sistema"></center>
            </form>
        
             <!-- /page content -->

                <!-- footer content -->
                <footer>
                    <div class="pull-right">
                        CMM CEINTEL - Admin Template by <a href="https://www.facebook.com/leandro.lopesleal.1">Leandro Leal</a>
                    </div>
                    <div class="clearfix"></div>
                </footer>
                <!-- /footer content -->
            </div>
        </div>

      <!-- jQuery -->
      <script src="../vendors/jquery/dist/jquery.min.js"></script>
      <!-- Bootstrap -->
      <script src="../vendors/bootstrap/dist/js/bootstrap.min.js"></script>
      <!-- FastClick -->
      <script src="../vendors/fastclick/lib/fastclick.js"></script>
      <!-- NProgress -->
      <script src="../vendors/nprogress/nprogress.js"></script>
      <!-- Custom Theme Scripts -->
      <script src="../build/js/custom.min.js"></script>
      <script>     
      $(document).ready(function() {
            function getData() {
              var dados = $('#log').val();
              if (dados == 'log.txt') {
                $.ajax({
                  url: "controla_log.php",
                  data: "arquivo="+dados
                }).done(function(data) {
                  var data = JSON.parse(data);
                  if (data.tipo == 'arquivo') {
                    $('#conteudo_log').val(data.conteudo); 
                  }
                });  
              } else {
                $.ajax({
                  url: "controla_log.php",
                  data: "arquivo="+dados
                }).done(function(data) {
                  var pasta = $('#log').val();
                  var arquivo = $('#arquivos').val();
                    $.ajax({
                        url: "controla_log.php",
                        data: "arquivo="+arquivo+"&pasta="+pasta
                    }).done(function(data) {
                        var data = JSON.parse(data);
                        if (data.tipo == 'arquivo') {
                          $('#conteudo_log').val(data.conteudo); 
                        }
                    });
                }); 
              }
            }
            getData();
            setInterval(getData, 1000);   

            $('#log').change(function(){
              var dados = $('#log').val();
              $.ajax({
                  url: "controla_log.php",
                  data: "arquivo="+dados
                }).done(function(data) {
                  var data = JSON.parse(data);
                    $('#arquivos').html(data.conteudo); 
                }); 
            });       
        });
        </script>
   </body>
</html>