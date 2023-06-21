// Score ZAP against OWASP Juice Shop
//
// You will need to have run the ZAP AJAX Spider against a local instance of Juice Shop

// Expected results sourced from manual exploring + the AJAX Spider

var expectedResults = [
	"GET http://cdnjs.cloudflare.com/ajax/libs/cookieconsent2/3.1.0/cookieconsent.min.css",
	"GET http://cdnjs.cloudflare.com/ajax/libs/cookieconsent2/3.1.0/cookieconsent.min.js",
	"GET http://cdnjs.cloudflare.com/ajax/libs/jquery/2.2.4/jquery.min.js",
	"GET http://localhost:3000/",
	"GET http://localhost:3000/ae.svg",
	"GET http://localhost:3000/api/Challenges/(name)",
	"GET http://localhost:3000/api/Feedbacks/",
	"GET http://localhost:3000/api/Quantitys/",
	"GET http://localhost:3000/assets/i18n/en.json",
	"GET http://localhost:3000/assets/public/favicon_js.ico",
	"GET http://localhost:3000/assets/public/images/carousel/1.jpg",
	"GET http://localhost:3000/assets/public/images/carousel/2.jpg",
	"GET http://localhost:3000/assets/public/images/carousel/3.jpg",
	"GET http://localhost:3000/assets/public/images/carousel/4.jpg",
	"GET http://localhost:3000/assets/public/images/carousel/5.png",
	"GET http://localhost:3000/assets/public/images/carousel/6.jpg",
	"GET http://localhost:3000/assets/public/images/carousel/7.jpg",
	"GET http://localhost:3000/assets/public/images/hackingInstructor.png",
	"GET http://localhost:3000/assets/public/images/JuiceShop_Logo.png",
	"GET http://localhost:3000/assets/public/images/products/apple_juice.jpg",
	"GET http://localhost:3000/assets/public/images/products/apple_pressings.jpg",
	"GET http://localhost:3000/assets/public/images/products/artwork2.jpg",
	"GET http://localhost:3000/assets/public/images/products/banana_juice.jpg",
	"GET http://localhost:3000/assets/public/images/products/carrot_juice.jpeg",
	"GET http://localhost:3000/assets/public/images/products/eggfruit_juice.jpg",
	"GET http://localhost:3000/assets/public/images/products/fan_facemask.jpg",
	"GET http://localhost:3000/assets/public/images/products/fan_girlie.jpg",
	"GET http://localhost:3000/assets/public/images/products/fruit_press.jpg",
	"GET http://localhost:3000/assets/public/images/products/green_smoothie.jpg",
	"GET http://localhost:3000/assets/public/images/products/lemon_juice.jpg",
	"GET http://localhost:3000/assets/public/images/products/melon_bike.jpeg",
	"GET http://localhost:3000/assets/public/images/products/permafrost.jpg",
	"GET http://localhost:3000/az.svg",
	"GET http://localhost:3000/font-mfizz.woff",
	"GET http://localhost:3000/ftp/legal.md",
	"GET http://localhost:3000/main.js",
	"GET http://localhost:3000/MaterialIcons-Regular.woff2",
	"GET http://localhost:3000/polyfills.js",
	"GET http://localhost:3000/rest/admin/application-configuration",
	"GET http://localhost:3000/rest/admin/application-version",
	"GET http://localhost:3000/rest/captcha/",
	"GET http://localhost:3000/rest/languages",
	"GET http://localhost:3000/rest/products/1/reviews",
	"GET http://localhost:3000/rest/products/search(q)",
	"GET http://localhost:3000/rest/user/whoami",
	"GET http://localhost:3000/runtime.js",
	"GET http://localhost:3000/socket.io/(EIO,sid,t,transport)",
	"POST http://localhost:3000/socket.io/(EIO,sid,t,transport)(40)",
	"GET http://localhost:3000/socket.io/(EIO,sid,transport)",
	"GET http://localhost:3000/socket.io/(EIO,t,transport)",
	"GET http://localhost:3000/styles.css",
	"GET http://localhost:3000/tutorial.js",
	"GET http://localhost:3000/vendor.js"
]

function listChildren(node, array) {
    var j;
    var parentName = node.getHierarchicNodeName();
    for (j=0;j<node.getChildCount();j++) {
        var child = node.getChildAt(j);
        if (child.isLeaf()) {
          var nodeName = child.getNodeName();
          var idx = nodeName.indexOf(':');
          var method = nodeName.substring(0, idx);
          var name = nodeName.substring(idx+1);
          if (! name.startsWith('/')) {
            name = '/' + name;
          }
          array.push(method + " " + parentName + name);
        } else {
           listChildren(child, array);
        }
    }
}

root = org.parosproxy.paros.model.Model.getSingleton().
        getSession().getSiteTree().getRoot();

var foundUrls = []
listChildren(root, foundUrls);

// This would be so much easier using Sets, but they are not available in Nashorn :/
allResults = [];
for (var i=0; i < expectedResults.length; i++) {
  var item = expectedResults[i];
  allResults.push(item);
}
for (var i=0; i < foundUrls.length; i++) {
  var item = foundUrls[i];
  if (allResults.indexOf(item) == -1) {
    allResults.push(item);
  }
}
allResults.sort();

var pass = 0;
var fail = 0;
var newu = 0;

var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');

var yamlFile = "/zap/wrk/all.yml";
var fw = new FileWriter(yamlFile);
var pw = new PrintWriter(fw);

pw.println('section: All URLs');
pw.println('target: OWASP Juice Shop');
pw.println('details:');

for (var i=0; i < allResults.length; i++) {
  var item = allResults[i];
  if (item.length == 0) {
    continue;
  }
  pw.println ('- path: ' + item);
  if (expectedResults.indexOf(item) > -1) {
    if (foundUrls.indexOf(item) > -1) {
      pw.println ('  ajax: Pass');
      pass +=1;
    } else {
      pw.println ('  ajax: FAIL');
      fail +=1;
    }
  } else {
    pw.println ('  ajax: New');
    newu +=1;
  }
}

var total = pass + fail;
pw.println('tests: ' + total);
pw.println('passes: ' + pass);
pw.println('fails: ' + fail);
pw.println('score: ' +  Math.round(pass * 100 / total) + '%');

print('tests: ' + total);
print('passes: ' + pass);
print('fails: ' + fail);
print('new: ' + newu);
print('Done');

pw.close();
