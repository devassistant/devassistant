import javax.faces.bean.ManagedBean;
import javax.faces.bean.ViewScoped;

@ManagedBean
@ViewScoped
public class Index {

	public Index(){
	}
	
	public String getText(){
		return "This text comes from backing bean.";
	}
}

