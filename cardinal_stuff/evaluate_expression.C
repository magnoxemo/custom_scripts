#include <iostream>
#include <string>
#include <vector>
#include <cstring>


//this might not be necessary when I implement it in moose
void get_input(std::vector<std::string>& expression);

void evaluate_expression(const std::vector<std::string>& expression) ;

template <typename T> void print(const std::vector<T>& expression);

void find_parentheses_prioprity(std::vector<std::string>& parenthesis);

int main(){
    //not user friendly at all but right now I am presuming
    //that the expression needs to be separated by a space
    std::vector<std::string> _expression {"( ( ( A and B ) || ( ( ) ) ( ) ( C & D ) || C ) & E )"};
    get_input(_expression);
    evaluate_expression(_expression);
    return 0;

}

void
evaluate_expression(const std::vector<std::string>& expression){

    std::vector<std::pair<std::string, int>> execution_orders;
    std::vector<std::string> parentheses;
    std::vector<std::string> logical_operators;
    std::vector<std::string> set_names;

    for (const auto var:expression){
        if (var == "(" or var== ")" )
            parentheses.push_back(var);
        else if (var == "and" or var =="or" or var =="&" or var =="||")
            logical_operators.push_back(var);
        else
            set_names.push_back(var);
    }
//    print(set_names);
//    print(parentheses);
//    print(logical_operators);
        find_parentheses_prioprity(parentheses);

    //okay now that my implementation can seperate the parentheses operators and names
    // i need to focus on how to order them in a correct way I can start by finding the pairs in parentheses

}

template <typename T>
void print(const std::vector<T>& expression){
    for (const auto &_:expression)
        std::cout<< _<<" ";
    std::cout<<"\n";
}

void find_parentheses_prioprity(std::vector<std::string>& parentheses){
        for (int i =0; i <parentheses.size();i++)
        {
            if ( parentheses[i] == "(" and parentheses[i+1]== ")" ){
                std::cout<<"("<<i+1<<" "<<i+2<<") ";
                parentheses[i] = "--";
                parentheses[i+1]= "--";
            }
        }
        std::cout<<"\n";
}

void get_input(std::vector<std::string>& expression) {
    std::string cp = expression[0];
    expression.clear();
    std::string str = "";
    for (size_t i = 0; i < cp.size(); i++) {
        if (cp[i] == ' ') {
            if (!str.empty()) {
                expression.push_back(str);
                str.clear();
            }
        } else {
            str += cp[i];
        }
    }
    if (!str.empty()) {
        expression.push_back(str);
    }
}





